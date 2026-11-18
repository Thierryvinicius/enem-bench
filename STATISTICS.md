# Statistics

Every run writes `results/<timestamp>/answers.csv`, and `Rscript analysis/analysis.R results/<timestamp>` turns it into the files below. This page explains what each one tells you and how to read it.

All p-values in the same file are adjusted with the Holm method, because several models or pairs are tested together. Read the `p_adjusted` column and use 0.05 as the usual threshold.

## Accuracy

**`accuracy_overall.csv`, `accuracy_model.png`**: share of correct answers per model, with a 95% Wilson confidence interval. If the intervals of two models overlap, the difference may be noise. The dashed line is random guessing (20%).

**`accuracy_area.csv`, `accuracy_area.png`**: accuracy per model and area (`languages`, `humanities`, `natural_sciences`, `mathematics`). Shows where each model is strong or weak.

**`accuracy_image.csv`**: accuracy on questions with and without a figure. Descriptive only; use `effects.csv` for a test that adjusts for area.

## Comparing models

**`mcnemar.csv`**: whether two models really differ. Both models answer the same questions, so the test looks only at those where one is right and the other wrong. `p_adjusted` below 0.05 means a real difference. A high value does not prove the models are equal, only that the sample is too small to tell.

## Against chance

**`vs_chance.csv`, `vs_chance_area.csv`**: one-sided binomial test of each model against random guessing (20%). `above_chance` is true when `p_adjusted` is below 0.05. If it is false, the model is indistinguishable from guessing, which is common for math with small models.

## Effects of images and model type

**`effects.csv`**: logistic regression with odds ratios.

- `image_effect_adjusted_for_model_and_area`: effect of having a figure, after accounting for the model and the area.
- `base_vs_instruct_adjusted_for_area_and_image`: effect of the model type (only when the run has both).

An odds ratio of 1 means no effect, below 1 hurts, above 1 helps. If the interval `lo`–`hi` contains 1, the effect is not significant.

**`image_fisher.csv`**: Fisher exact test of accuracy with vs without figure, per model. `p_adjusted` below 0.05 means the figure changes that model's accuracy.

## Letter bias

**`letter_bias.csv`, `letter_bias.png`**: whether a model has a favorite letter regardless of the question.

- `pred_A` to `pred_E`: share of the model's answers that were each letter.
- `top_letter`, `top_share`: the most chosen letter and its share.
- `chisq`, `p_value`, `p_adjusted`: chi-square test of the predicted letters against the distribution of the answer key. Small values mean bias.

In the plot, the blue bars are the share of each letter predicted by the model and the red marks are the share of each letter in the answer key. The further the bars are from the marks, the stronger the bias. A biased model can still score above chance if its favorite letter happens to be right often, and a model without bias is not necessarily right.

## Calibration

The model never writes an answer. It picks the letter with the highest logit, and `prob_A` to `prob_E` in `answers.csv` are the softmax of those logits over the answer letters. Calibration checks whether that confidence matches reality. Runs made before these columns existed skip this section.

**`calibration_summary.csv`**: one row per model.

- `accuracy` and `mean_confidence`: if the confidence is above the accuracy, the model is overconfident.
- `brier` and `logloss`: error of the probabilities, lower is better. They separate weak models better than accuracy does.
- `ece`: expected calibration error, the average gap between confidence and accuracy across bins. Closer to 0 is better.
- `conf_when_right` and `conf_when_wrong`: a useful model is much more confident when right than when wrong. If both are similar, its confidence says nothing.

**`calibration_bins.csv`, `calibration.png`**: accuracy per confidence bin. The x axis is the confidence of the model and the y axis is how often it was right in that bin. Points on the dashed diagonal are calibrated, below it are overconfident. The size of each point is the number of questions in the bin: a far-off point that is tiny may be luck, a far-off point that is large is real miscalibration.
