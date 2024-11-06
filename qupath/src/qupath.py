import itertools
import json

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import LineString, Point, Polygon


def load_geojson(geojson_path=None, geojson_text=None):
    if geojson_path is not None:
        with open(geojson_path, "r") as f:
            geojson_data = json.load(f)
        # Convert GeoJSON to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
    else:
        geojson_data = json.loads(geojson_text)
        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
    return gdf


########################################################################################################################
# Buffer
########################################################################################################################

def add_buffers(gdf, buffer_distance):
    beg_buffers = []
    end_buffers = []
    for line in gdf.geometry:
        beg_point = Point(line.coords[0])
        end_point = Point(line.coords[-1])
        beg_buffers.append(beg_point.buffer(buffer_distance))
        end_buffers.append(end_point.buffer(buffer_distance))

    gdf["beg_buffer"] = gpd.GeoSeries(beg_buffers)
    gdf["end_buffer"] = gpd.GeoSeries(end_buffers)
    return gdf


def plot_geometries(ax, gdf):
    """
    Helper function to plot polygons in red and each line in a unique color from a specified colormap range.

    Parameters:
    - ax: matplotlib axis to plot on.
    - im: Image to display as the background.
    - gdf: GeoDataFrame containing the geometries to plot.
    - colormap: Name of the colormap to use for lines.
    - colormap_start: Start of the colormap range (between 0.0 and 1.0).
    - colormap_end: End of the colormap range (between 0.0 and 1.0).
    """
    default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    color_cycle = itertools.cycle(default_colors)

    for i in range(gdf.shape[0]):
        color = next(color_cycle)
        gdf.geometry.loc[[i]].plot(ax=ax, color=color)
    return ax


def plot_lines_polygons(gdf_polygons, gdf_lines, buffer_distance=50, xlim=None, ylim=None, figsize=(10, 10)):
    fig, axes = plt.subplots(1, 1, figsize=figsize)
    axes = plot_geometries(axes, gdf_polygons)
    axes = plot_geometries(axes, gdf_lines)
    gdf_lines_buffers = add_buffers(gdf_lines.copy(), buffer_distance)
    gdf_lines_buffers.beg_buffer.plot(ax=axes, color="red", alpha=0.2)
    gdf_lines_buffers.end_buffer.plot(ax=axes, color="blue", alpha=0.2)

    axes.set_xlim(xlim)
    axes.set_ylim(ylim)
    plt.close(fig)
    return fig


def merge_lines(i_gdf_line, j_gdf_line):
    if i_gdf_line.beg_buffer.intersects(j_gdf_line.beg_buffer):
        merged_coords = list(i_gdf_line.geometry.coords[::-1]) + list(j_gdf_line.geometry.coords)
        return LineString(merged_coords)
    elif i_gdf_line.beg_buffer.intersects(j_gdf_line.end_buffer):
        merged_coords = list(i_gdf_line.geometry.coords[::-1]) + list(j_gdf_line.geometry.coords[::-1])
        return LineString(merged_coords)
    elif i_gdf_line.end_buffer.intersects(j_gdf_line.beg_buffer):
        merged_coords = list(i_gdf_line.geometry.coords) + list(j_gdf_line.geometry.coords)
        return LineString(merged_coords)
    elif i_gdf_line.end_buffer.intersects(j_gdf_line.end_buffer):
        merged_coords = list(i_gdf_line.geometry.coords) + list(j_gdf_line.geometry.coords[::-1])
        return LineString(merged_coords)
    else:
        return False


def merge_buffers(gdf_polygons, gdf_lines, buffer_distance=50):
    gdf_lines_0 = []
    gdf_polygons_0 = []
    gdf_lines = add_buffers(gdf_lines, buffer_distance=buffer_distance)

    # merge self polygons
    for i in gdf_lines.index:
        i_beg_buffer = gdf_lines.at[i, "beg_buffer"]
        i_end_buffer = gdf_lines.at[i, "end_buffer"]
        if i_beg_buffer.intersects(i_end_buffer):
            gdf_polygons_0.append(Polygon(gdf_lines.at[i, "geometry"]))
            gdf_lines.drop(i, inplace=True)
    gdf_lines = gdf_lines.reset_index(drop=True)

    # merge lines
    index_merged = []
    for i in gdf_lines.index:
        if i in index_merged:
            continue
        i_gdf_line = gdf_lines.loc[i]
        i_merged = False
        j_indecies = [index for index in gdf_lines.index if (index not in index_merged) and (index > i)]
        for j in j_indecies:
            j_gdf_line = gdf_lines.loc[j]
            merged_line = merge_lines(i_gdf_line, j_gdf_line)
            if merged_line:
                gdf_lines_0.append(merged_line)
                i_merged = True
                index_merged.append(j)
                break
        if not i_merged:
            gdf_lines_0.append(i_gdf_line.geometry)

    gdf_lines_0 = gpd.GeoDataFrame(gdf_lines_0, columns=["geometry"], crs=gdf_lines.crs)
    gdf_polygons_0 = gpd.GeoDataFrame(gdf_polygons_0, columns=["geometry"], crs=gdf_lines.crs)

    return (
        pd.concat([gdf_polygons, gdf_polygons_0], ignore_index=True).set_geometry("geometry"),
        gdf_lines_0.set_geometry("geometry"),
    )
