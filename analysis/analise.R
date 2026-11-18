suppressPackageStartupMessages({
  library(dplyr); library(ggplot2); library(readr); library(tidyr)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Uso: Rscript analysis/analise.R results/<data-hora>")
dir_run <- args[1]

d <- read_csv(file.path(dir_run, "respostas.csv"), show_col_types = FALSE)
d$acerto <- as.logical(d$acerto)

wilson <- function(k, n, z = 1.96) {
  p <- k / n
  c(lo = (p + z^2 / (2 * n) - z * sqrt(p * (1 - p) / n + z^2 / (4 * n^2))) / (1 + z^2 / n),
    hi = (p + z^2 / (2 * n) + z * sqrt(p * (1 - p) / n + z^2 / (4 * n^2))) / (1 + z^2 / n))
}

geral <- d |>
  group_by(modelo, grupo, tipo) |>
  summarise(n = n(), acertos = sum(acerto), acuracia = mean(acerto), .groups = "drop")
ic <- t(mapply(wilson, geral$acertos, geral$n))
geral$lo <- ic[, "lo"]
geral$hi <- ic[, "hi"]
write_csv(geral, file.path(dir_run, "acuracia_geral.csv"))
print(geral)

p1 <- ggplot(geral, aes(reorder(modelo, acuracia), acuracia, fill = grupo, alpha = tipo)) +
  geom_col() +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = .25, alpha = 1) +
  geom_hline(yintercept = 0.2, linetype = "dashed") +
  scale_alpha_manual(values = c(base = 0.55, instruct = 1)) +
  coord_flip() +
  scale_y_continuous(labels = scales::percent, limits = c(0, 1)) +
  labs(x = NULL, y = "Acurácia", title = "ENEM: acurácia por modelo",
       subtitle = "Linha tracejada = chute aleatório (20%)") +
  theme_minimal()
ggsave(file.path(dir_run, "acuracia_modelo.png"), p1, width = 8, height = 5, dpi = 150)

area <- d |>
  group_by(modelo, area) |>
  summarise(acuracia = mean(acerto), n = n(), .groups = "drop")
write_csv(area, file.path(dir_run, "acuracia_area.csv"))
p2 <- ggplot(area, aes(area, modelo, fill = acuracia)) +
  geom_tile() +
  geom_text(aes(label = sprintf("%.0f%%", 100 * acuracia))) +
  scale_fill_gradient(low = "#f7fbff", high = "#08519c", limits = c(0, 1)) +
  labs(x = NULL, y = NULL, fill = "Acurácia", title = "Acurácia por área") +
  theme_minimal()
ggsave(file.path(dir_run, "acuracia_area.png"), p2, width = 8, height = 5, dpi = 150)

imagem <- d |>
  group_by(modelo, tem_imagem) |>
  summarise(acuracia = mean(acerto), n = n(), .groups = "drop")
write_csv(imagem, file.path(dir_run, "acuracia_imagem.csv"))

w <- d |>
  select(id, modelo, acerto) |>
  pivot_wider(names_from = modelo, values_from = acerto)
mods <- setdiff(names(w), "id")
if (length(mods) >= 2) {
  res <- do.call(rbind, lapply(combn(mods, 2, simplify = FALSE), function(p) {
    a <- w[[p[1]]]
    b <- w[[p[2]]]
    ok <- !is.na(a) & !is.na(b)
    tab <- table(factor(a[ok], c(TRUE, FALSE)), factor(b[ok], c(TRUE, FALSE)))
    data.frame(a = p[1], b = p[2], p_valor = suppressWarnings(mcnemar.test(tab)$p.value))
  }))
  res$p_ajust <- p.adjust(res$p_valor, method = "holm")
  write_csv(res, file.path(dir_run, "mcnemar.csv"))
  print(res)
}
