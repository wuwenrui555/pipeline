library(tidyverse)
library(fs)
library(gghalves)
library(stringr)

# Alignment parameters #####
error_dir <- "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/data/20250112_alignment_valis/error_df/"
error_files <- fs::dir_ls(error_dir, recurse = TRUE, regexp = "[.]csv")

error_df <- error_files %>%
    map(~ read_csv(.x, show_col_types = FALSE)[2, ]) %>%
    bind_rows()

p_df <- error_df %>%
    select(id, matches("_D$"), matches("_rTRE")) %>%
    pivot_longer(-id) %>%
    filter(str_detect(name, "mean", negate = TRUE)) %>%
    separate(name, into = c("mode", "param"), sep = "_(?=(D)|(rTRE))") %>%
    mutate(
        across(mode, ~ factor(.x, levels = c("original", "rigid", "non_rigid"))),
        tma = id %>% str_extract("TMA\\d+")
    ) %>%
    group_by(id, param) %>%
    mutate(min = value == min(value)) %>%
    group_by(tma) %>%
    mutate(tma = str_glue("{tma} ({n_distinct(id)})")) %>%
    arrange(min)

p <- p_df %>%
    ggplot(aes(x = id, y = value, shape = mode, color = min)) +
    geom_point(position = position_dodge(width = 0.5), size = 3) +
    facet_grid(param ~ tma, scales = "free", space = "free_x") +
    theme(
        strip.clip = "off",
        axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5),
    ) +
    labs(x = NULL, y = NULL, color = "Minimum", shape = "Mode")
p
output_dir <- "/mnt/nfs/home/wenruiwu/projects/bidmc-jiang-rcc/output/figure/valis_alignment/"
ggsave(fs::path(output_dir, "valis_alignment_re=TMA003_finally.png"), p, width = 30, height = 10, dpi = 300)

# Signal comparison #####
data_dir <- "/mnt/nfs/home/wenruiwu/pipeline/alignment/data/output/cell_feature/data_scale"

data_ldf <- fs::dir_ls(data_dir) %>%
    map(~ mutate(
        read_csv(.x, show_col_types = FALSE),
        mode = fs::path_ext_remove(fs::path_file(.x))
    )) %>%
    bind_rows() %>%
    pivot_longer(c(DAPI, CD3e))


marker <- "CD3e"
data_ldf_marker <- data_ldf %>%
    filter(name == marker)
data_wdf_marker <- data_ldf_marker %>%
    pivot_wider(names_from = mode, values_from = value)

p <- bind_rows(
    data_ldf_marker %>%
        filter(mode %in% c("sift", "non_rigid")) %>%
        mutate(x = "sift"),
    data_ldf_marker %>%
        filter(mode %in% c("rigid", "non_rigid")) %>%
        mutate(x = "rigid")
) %>%
    mutate(
        across(x, ~ factor(.x, levels = c("sift", "rigid", "non_rigid"))),
    ) %>%
    ggplot(aes(x = x, y = value, fill = mode)) +
    geom_half_violin(
        draw_quantiles = c(0.25, 0.50, 0.75),
        side = "l",
        data = ~ .x %>% filter(mode != "non_rigid")
    ) +
    geom_half_violin(
        draw_quantiles = c(0.25, 0.50, 0.75),
        side = "r",
        data = ~ .x %>% filter(mode == "non_rigid")
    ) +
    labs(title = marker)

non_vs_sift <- wilcox.test(data_wdf_marker$non_rigid, data_wdf_marker$sift, paired = TRUE)
non_vs_rigid <- wilcox.test(data_wdf_marker$rigid, data_wdf_marker$sift, paired = TRUE)

format_pvalue <- function(p_value, digits = 2) {
    if (p_value < 2.2e-16) {
        formatted <- glue::glue("p < 2.2{paste0(rep(0, digits-2), collapse = '')}e-16")
    } else {
        formatted_p <- sprintf(glue::glue("%.{digits}g"), p_value)
        if (str_detect(formatted_p, "e-")) {
            num <- sprintf(
                glue::glue("%.{digits - 1}f"),
                as.numeric((str_extract(formatted_p, ".+(?=e-)")))
            )
            exp <- str_extract(formatted_p, "e-\\d+")
            formatted <- glue::glue("p = {num}{exp}")
        } else {
            formatted <- glue::glue("p = {formatted_p}")
        }
    }
    return(formatted)
}



pdata_label <- tibble(
    x = c("rigid", "sift"),
    y = max(p$data$value) * 1.01,
    label = c(
        format_pvalue(non_vs_rigid$p.value),
        format_pvalue(non_vs_sift$p.value)
    )
)

p +
    geom_text(
        aes(x = x, y = y, label = label),
        vjust = 0,
        hjust = 0.5,
        inherit.aes = FALSE,
        data = pdata_label,
    ) +
    labs(x = "vs non_rigid", y = "Signal Intensity") +
    theme_bw() +
    theme(plot.title = element_text(hjust = 0.5))


## log1p

marker <- "DAPI"
data_ldf_marker <- data_ldf %>%
    filter(name == marker)
data_wdf_marker <- data_ldf_marker %>%
    pivot_wider(names_from = mode, values_from = value)

p <- bind_rows(
    data_ldf_marker %>%
        filter(mode %in% c("sift", "non_rigid")) %>%
        mutate(x = "sift", value = log1p(value)),
    data_ldf_marker %>%
        filter(mode %in% c("rigid", "non_rigid")) %>%
        mutate(x = "rigid", value = log1p(value))
) %>%
    mutate(
        across(x, ~ factor(.x, levels = c("sift", "rigid", "non_rigid"))),
    ) %>%
    ggplot(aes(x = x, y = value, fill = mode)) +
    geom_half_violin(
        draw_quantiles = c(0.25, 0.50, 0.75),
        side = "l",
        data = ~ .x %>% filter(mode != "non_rigid")
    ) +
    geom_half_violin(
        draw_quantiles = c(0.25, 0.50, 0.75),
        side = "r",
        data = ~ .x %>% filter(mode == "non_rigid")
    ) +
    labs(title = marker)

non_vs_sift <- wilcox.test(data_wdf_marker$non_rigid, data_wdf_marker$sift, paired = TRUE)
non_vs_rigid <- wilcox.test(data_wdf_marker$rigid, data_wdf_marker$sift, paired = TRUE)

format_pvalue <- function(p_value, digits = 2) {
    if (p_value < 2.2e-16) {
        formatted <- glue::glue("p < 2.2{paste0(rep(0, digits-2), collapse = '')}e-16")
    } else {
        formatted_p <- sprintf(glue::glue("%.{digits}g"), p_value)
        if (str_detect(formatted_p, "e-")) {
            num <- sprintf(
                glue::glue("%.{digits - 1}f"),
                as.numeric((str_extract(formatted_p, ".+(?=e-)")))
            )
            exp <- str_extract(formatted_p, "e-\\d+")
            formatted <- glue::glue("p = {num}{exp}")
        } else {
            formatted <- glue::glue("p = {formatted_p}")
        }
    }
    return(formatted)
}

pdata_label <- tibble(
    x = c("rigid", "sift"),
    y = max(p$data$value) * 1.01,
    label = c(
        format_pvalue(non_vs_rigid$p.value),
        format_pvalue(non_vs_sift$p.value)
    )
)

p +
    geom_text(
        aes(x = x, y = y, label = label),
        vjust = 0,
        hjust = 0.5,
        inherit.aes = FALSE,
        data = pdata_label,
    ) +
    labs(x = "vs non_rigid", y = "Signal Intensity (log1p)") +
    theme_bw() +
    theme(plot.title = element_text(hjust = 0.5))
