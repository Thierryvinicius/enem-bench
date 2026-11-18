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

letters_all <- c("A", "B", "C", "D", "E")
chance <- 0.2

chance_tab <- function(df, by) {
  df |>
    group_by(across(all_of(by))) |>
    summarise(n = n(), hits = sum(correct), accuracy = mean(correct), .groups = "drop") |>
    rowwise() |>
    mutate(p_value = binom.test(hits, n, p = chance, alternative = "greater")$p.value) |>
    ungroup() |>
    mutate(p_adjusted = p.adjust(p_value, method = "holm"),
           above_chance = p_adjusted < 0.05)
}
vs_chance <- chance_tab(d, "model")
write_csv(vs_chance, file.path(dir_run, "vs_chance.csv"))
print(vs_chance)
vs_chance_area <- chance_tab(d, c("model", "area"))
write_csv(vs_chance_area, file.path(dir_run, "vs_chance_area.csv"))

tidy_glm <- function(fit, label) {
  co <- summary(fit)$coefficients
  ci <- suppressMessages(confint.default(fit))
  data.frame(analysis = label, term = rownames(co)[-1],
             odds_ratio = exp(co[-1, "Estimate"]),
             lo = exp(ci[-1, 1]), hi = exp(ci[-1, 2]),
             p_value = co[-1, "Pr(>|z|)"], row.names = NULL)
}
d$has_image_f <- factor(d$has_image, levels = c(0, 1), labels = c("no_image", "image"))
effects <- list()
if (n_distinct(d$has_image_f) > 1) {
  fit_img <- glm(correct ~ model + area + has_image_f, data = d, family = binomial)
  effects$image <- tidy_glm(fit_img, "image_effect_adjusted_for_model_and_area")
}
if (n_distinct(d$type) > 1) {
  fit_type <- glm(correct ~ type + area + has_image_f, data = d, family = binomial)
  effects$type <- tidy_glm(fit_type, "base_vs_instruct_adjusted_for_area_and_image")
}
if (length(effects) > 0) {
  effects <- do.call(rbind, effects)
  write_csv(effects, file.path(dir_run, "effects.csv"))
  print(effects)
}

fisher_img <- d |>
  group_by(model) |>
  filter(n_distinct(has_image_f) > 1) |>
  summarise(
    acc_no_image = mean(correct[has_image_f == "no_image"]),
    acc_image = mean(correct[has_image_f == "image"]),
    p_value = fisher.test(table(factor(correct, c(TRUE, FALSE)), has_image_f))$p.value,
    .groups = "drop") |>
  mutate(p_adjusted = p.adjust(p_value, method = "holm"))
if (nrow(fisher_img) > 0) write_csv(fisher_img, file.path(dir_run, "image_fisher.csv"))

pred_d <- d |> filter(!is.na(prediction), prediction %in% letters_all)
answer_share <- prop.table(table(factor(d$answer[!duplicated(d$id)], letters_all)))
bias <- do.call(rbind, lapply(split(pred_d, pred_d$model), function(g) {
  counts <- table(factor(g$prediction, letters_all))
  share <- prop.table(counts)
  expected <- as.numeric(answer_share)
  keep <- expected > 0
  test <- suppressWarnings(chisq.test(as.numeric(counts)[keep], p = expected[keep] / sum(expected[keep])))
  out <- data.frame(model = g$model[1], n = nrow(g),
                    t(setNames(as.numeric(share), paste0("pred_", letters_all))),
                    top_letter = names(which.max(counts)),
                    top_share = max(share),
                    chisq = unname(test$statistic), p_value = test$p.value)
  out
}))
rownames(bias) <- NULL
bias$p_adjusted <- p.adjust(bias$p_value, method = "holm")
write_csv(bias, file.path(dir_run, "letter_bias.csv"))
print(bias)

bias_long <- bias |>
  select(model, starts_with("pred_")) |>
  pivot_longer(-model, names_to = "letter", values_to = "share") |>
  mutate(letter = sub("pred_", "", letter))
answer_df <- data.frame(letter = letters_all, share = as.numeric(answer_share))
p3 <- ggplot(bias_long, aes(letter, share)) +
  geom_col(fill = "#08519c") +
  geom_point(data = answer_df, aes(letter, share), shape = 95, size = 8, colour = "red", inherit.aes = FALSE) +
  facet_wrap(~model) +
  scale_y_continuous(labels = scales::percent) +
  labs(x = NULL, y = "Share of predictions", title = "Letter bias",
       subtitle = "Red mark = share of each letter in the answer key") +
  theme_minimal()
ggsave(file.path(dir_run, "letter_bias.png"), p3, width = 9, height = 6, dpi = 150)

prob_cols <- paste0("prob_", letters_all)
if (all(prob_cols %in% names(d))) {
  cal <- d |> filter(if_all(all_of(prob_cols), ~ !is.na(.x)), answer %in% letters_all)
  pm <- as.matrix(cal[, prob_cols])
  onehot <- sapply(letters_all, function(l) as.numeric(cal$answer == l))
  cal$brier <- rowSums((pm - onehot)^2)
  cal$p_answer <- pm[cbind(seq_len(nrow(cal)), match(cal$answer, letters_all))]
  cal$logloss <- -log(pmax(cal$p_answer, 1e-12))
  cal$confidence <- apply(pm, 1, max)

  cal$bin <- cut(cal$confidence, breaks = seq(0.2, 1, length.out = 9), include.lowest = TRUE)
  bins <- cal |>
    group_by(model, bin) |>
    summarise(n = n(), confidence = mean(confidence), accuracy = mean(correct), .groups = "drop")
  write_csv(bins, file.path(dir_run, "calibration_bins.csv"))

  cal_summary <- cal |>
    group_by(model) |>
    summarise(n = n(), accuracy = mean(correct), mean_confidence = mean(confidence),
              brier = mean(brier), logloss = mean(logloss), .groups = "drop") |>
    left_join(bins |> group_by(model) |>
                summarise(ece = sum(n * abs(accuracy - confidence)) / sum(n), .groups = "drop"),
              by = "model")
  conf_split <- cal |>
    group_by(model) |>
    summarise(conf_when_right = mean(confidence[correct]),
              conf_when_wrong = mean(confidence[!correct]), .groups = "drop")
  cal_summary <- left_join(cal_summary, conf_split, by = "model")
  write_csv(cal_summary, file.path(dir_run, "calibration_summary.csv"))
  print(cal_summary)

  p4 <- ggplot(bins, aes(confidence, accuracy, size = n)) +
    geom_abline(linetype = "dashed") +
    geom_point(alpha = .8, colour = "#08519c") +
    facet_wrap(~model) +
    scale_x_continuous(labels = scales::percent, limits = c(0, 1)) +
    scale_y_continuous(labels = scales::percent, limits = c(0, 1)) +
    labs(x = "Mean confidence", y = "Accuracy", size = "Questions",
         title = "Calibration", subtitle = "Dashed line = perfectly calibrated") +
    theme_minimal()
  ggsave(file.path(dir_run, "calibration.png"), p4, width = 9, height = 6, dpi = 150)
} else {
  message("answers.csv has no prob_* columns (older run); skipping calibration")
}
