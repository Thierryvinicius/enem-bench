suppressPackageStartupMessages({
  library(dplyr); library(ggplot2); library(readr); library(tidyr)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Usage: Rscript analysis/analysis.R results/<timestamp>")
dir_run <- args[1]

d <- read_csv(file.path(dir_run, "answers.csv"), show_col_types = FALSE)
d$correct <- as.logical(d$correct)

wilson <- function(k, n, z = 1.96) {
  p <- k / n
  c(lo = (p + z^2 / (2 * n) - z * sqrt(p * (1 - p) / n + z^2 / (4 * n^2))) / (1 + z^2 / n),
    hi = (p + z^2 / (2 * n) + z * sqrt(p * (1 - p) / n + z^2 / (4 * n^2))) / (1 + z^2 / n))
}

overall <- d |>
  group_by(model, group, type) |>
  summarise(n = n(), hits = sum(correct), accuracy = mean(correct), .groups = "drop")
ci <- t(mapply(wilson, overall$hits, overall$n))
overall$lo <- ci[, "lo"]
overall$hi <- ci[, "hi"]
write_csv(overall, file.path(dir_run, "accuracy_overall.csv"))
print(overall)

p1 <- ggplot(overall, aes(reorder(model, accuracy), accuracy, fill = group, alpha = type)) +
  geom_col() +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = .25, alpha = 1) +
  geom_hline(yintercept = 0.2, linetype = "dashed") +
  scale_alpha_manual(values = c(base = 0.55, instruct = 1)) +
  coord_flip() +
  scale_y_continuous(labels = scales::percent, limits = c(0, 1)) +
  labs(x = NULL, y = "Accuracy", title = "ENEM: accuracy by model",
       subtitle = "Dashed line = random guessing (20%)") +
  theme_minimal()
ggsave(file.path(dir_run, "accuracy_model.png"), p1, width = 8, height = 5, dpi = 150)

area <- d |>
  group_by(model, area) |>
  summarise(accuracy = mean(correct), n = n(), .groups = "drop")
write_csv(area, file.path(dir_run, "accuracy_area.csv"))
p2 <- ggplot(area, aes(area, model, fill = accuracy)) +
  geom_tile() +
  geom_text(aes(label = sprintf("%.0f%%", 100 * accuracy))) +
  scale_fill_gradient(low = "#f7fbff", high = "#08519c", limits = c(0, 1)) +
  labs(x = NULL, y = NULL, fill = "Accuracy", title = "Acurácia por área") +
  theme_minimal()
ggsave(file.path(dir_run, "accuracy_area.png"), p2, width = 8, height = 5, dpi = 150)

image <- d |>
  group_by(model, has_image) |>
  summarise(accuracy = mean(correct), n = n(), .groups = "drop")
write_csv(image, file.path(dir_run, "accuracy_image.csv"))

w <- d |>
  select(id, model, correct) |>
  pivot_wider(names_from = model, values_from = correct)
models <- setdiff(names(w), "id")
if (length(models) >= 2) {
  res <- do.call(rbind, lapply(combn(models, 2, simplify = FALSE), function(p) {
    a <- w[[p[1]]]
    b <- w[[p[2]]]
    ok <- !is.na(a) & !is.na(b)
    tab <- table(factor(a[ok], c(TRUE, FALSE)), factor(b[ok], c(TRUE, FALSE)))
    data.frame(a = p[1], b = p[2], p_value = suppressWarnings(mcnemar.test(tab)$p.value))
  }))
  res$p_adjusted <- p.adjust(res$p_value, method = "holm")
  write_csv(res, file.path(dir_run, "mcnemar.csv"))
  print(res)
}
