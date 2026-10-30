"""Launch vehicle readiness analysis, rebuilt as one sigular script.
Reads MATLAB_Input and runs the Monte Carlo and Bayesian readiness analysis.
Saves plots, result tables, and the settings used for each run.
"""

# %% 1. Imports
# MATLAB references below use line numbers in:
#   MATLAB Baseline/mc_faulttree_bayes_demo_v13.m
# MATLAB helper functions are written inline here, from top to bottom.
from datetime import datetime
from pathlib import Path
import json #need for saving outputs
import warnings #gives warnings without ending the code

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import beta as beta_distribution


# %% 2. Input and output locations
# MATLAB lines 19-24: mfilename('fullpath') and fileparts(scriptPath).
# Resolve paths relative to this file, regardless of where Python is launched. Finds folder with the python script.
script_dir = Path(__file__).resolve().parent

# MATLAB line 26: inputFile = fullfile(scriptDir, "Inputs_sheet.xlsx").
# Read the workbook beside this script. Builds path to the input workbook
input_file = script_dir / "Inputs_sheet.xlsx"
input_sheet = "MATLAB_Input"

# Define output locations; section 21 creates the folders after the analysis.
# MATLAB lines 27-30 and 36: outputRoot, runStamp, runDir, tablesFile,
# and figuresDir. Folder creation/checks in lines 33-35 and 37 are deferred.
output_root = script_dir / "outputs"
run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
run_dir = output_root / f"run_{run_stamp}"
tables_file = run_dir / "results.xlsx"
figures_dir = run_dir / "figures"

# %% 3. Monte Carlo settings
# MATLAB line 16: rng(1), for the repeatable random seed.
random_seed = 1
rng = np.random.default_rng(random_seed)
# A fixed seed makes Python runs repeatable. It does not reproduce MATLAB's
# exact random draws, even when both programs use seed 1.

n_prior = 200_000       # MATLAB line 39: N = 200e3 (prior samples).
n_posterior = 50_000   # MATLAB line 40: Mpost = 50000 (posterior resamples).


# %% 4. Score-to-parameter mappings (unchanged from MATLAB v13)
# MATLAB lines 43-46: scoreLevels, muTLevels, mOLevels, and sOLevels.
# Corresponding positions in these arrays describe the same score level.
score_levels = np.array([0, 1, 2, 3, 4], dtype=float)

# Technical score -> base mean of the component success probability.
mu_t_levels = np.array([0.40, 0.60, 0.75, 0.88, 0.96])

# Organizational score -> multiplier on that mean and base Beta strength.
m_o_levels = np.array([0.90, 0.99, 1.03, 1.07, 1.10])
s_o_levels = np.array([4, 8, 12, 16, 20], dtype=float)


# %% 5. Lifecycle phase settings
# MATLAB lines 48-49: phaseLevels and lambdaLevels.
# Each phase uses the strength multiplier at the same position below.
phase_levels = ["SFR", "PDR", "CDR", "TRR", "SVR"]
lambda_levels = np.array([0.7, 1.0, 1.3, 1.6, 2.0])


# %% 6. Component and basic-event order
# MATLAB lines 51-58: componentOrder; line 60: basicEventOrder.
# Keep these lists aligned: each component corresponds to one failure event.
# Names match the MATLAB baseline and its input workbook.
component_order = ["Concept", "Design Verification", "Manufacturing", "Assembly and Integration", "Impl. Verification", "Operation Setup", "Operation Execution",]

basic_event_order = ["q_C", "q_Vd", "q_M", "q_I", "q_Vi", "q_S", "q_E"]


# %% 8. Load only the MATLAB_Input worksheet
# MATLAB line 32: assert(isfile(inputFile), ...).
if not input_file.is_file():
    raise FileNotFoundError(f"Input workbook not found: {input_file}")

# MATLAB lines 71-72: inputTable = readtable(inputFile, 'Sheet', ...).
# Keep blank cells empty and preserve text IDs such as NA.
input_table = pd.read_excel(
    input_file, sheet_name=input_sheet, dtype=object, keep_default_na=False,
)

# Clean text once, instead of repeating this for each column later.
# MATLAB stripText (lines 450-454). Numbers are converted back where needed.
for column in input_table.columns:
    input_table[column] = input_table[column].fillna("")
    input_table[column] = input_table[column].astype(str)
    input_table[column] = input_table[column].str.strip()


# %% 9. Read the lifecycle phase
# MATLAB lines 74-75 and 549-564: read and validate the lifecycle phase.
# Use the exact worksheet heading instead of searching for spelling variants.
phase_column = "Lifecycle Phase"
if phase_column not in input_table.columns:
    raise ValueError("MATLAB_Input needs a Lifecycle Phase column.")

# MATLAB lines 554-560: strip text, omit blanks, require one phase ignoring case.
phase_entries = input_table[phase_column].str.upper()
phase_entries = phase_entries[phase_entries != ""]
if phase_entries.empty:
    raise ValueError("Lifecycle phase column is empty.")
if phase_entries.nunique() != 1:
    raise ValueError("Lifecycle phase column must contain one unique phase.")

# MATLAB lines 558 and 561-563: select the phase and its lambda multiplier.
phase_name = phase_entries.iloc[0]
if phase_name not in phase_levels:
    raise ValueError(f"Unsupported lifecycle phase: {phase_name}")
phase_position = phase_levels.index(phase_name)
lambda_phase = lambda_levels[phase_position]


# %% 10. Reads and validates the test evidence and required failure probability
# MATLAB line 76 and helpers at lines 566-597.
# A setting can appear once or repeat, but all its nonblank values must agree.
settings = []
for setting_name in ["n_test", "k_fail", "q_req"]:
    if setting_name not in input_table.columns:
        raise ValueError(f"MATLAB_Input is missing column: {setting_name}")

    values = input_table[setting_name]
    values = values[values != ""]
    values = pd.to_numeric(values, errors="coerce")
    if values.empty:
        raise ValueError(f"Column {setting_name} is empty.")
    if not np.isfinite(values).all():
        raise ValueError(f"Column {setting_name} contains a nonnumeric or nonfinite value.")
    if values.nunique() != 1:
        raise ValueError(f"Column {setting_name} must contain one unique value.")

    # All nonblank entries agree, so use the first one.
    settings.append(float(values.iloc[0]))

# Assign the three values in the same order as the loop above.
n_test, k_fail, q_req = settings

# MATLAB lines 571-574: check integer counts and probability bounds.
if n_test < 0 or not n_test.is_integer():
    raise ValueError("n_test must be a nonnegative integer.")
if k_fail < 0 or not k_fail.is_integer():
    raise ValueError("k_fail must be a nonnegative integer.")
if k_fail > n_test:
    raise ValueError("k_fail must be <= n_test.")
if not 0 <= q_req <= 1:
    raise ValueError("q_req must be between 0 and 1.")
# Python-specific: store the validated whole-number counts as integers.
n_test = int(n_test)
k_fail = int(k_fail)


# %% 11. Cleans and checks the assessment rows
# MATLAB line 77 calls cleanMatlabInput (defined at lines 339-376).
# MATLAB lines 340-344: check the required assessment columns.
required_columns = ["Branch", "Component", "Indicator", "Cat", "Z", "RaterID"]
for column in required_columns:
    if column not in input_table.columns:
        raise ValueError(f"MATLAB_Input is missing column: {column}")

# Excel row 1 contains headers, so the first data row is row 2.
# MATLAB line 346: record SourceRow. Text was already cleaned in section 8.
input_table["SourceRow"] = np.arange(2, len(input_table) + 2)

# Ignore rows with no assessment content, even if they contain run settings.
# MATLAB lines 350-360: remove rows with no assessment information.
assessment_columns = required_columns.copy()
if "Status" in input_table.columns:
    assessment_columns.append("Status")

# Check one row at a time and collect the rows whose assessment cells are blank.
empty_rows = []
for row_index in input_table.index:
    assessment_values = input_table.loc[row_index, assessment_columns]
    if (assessment_values == "").all():
        empty_rows.append(row_index)

input_table = input_table.drop(index=empty_rows)
if input_table.empty:
    raise ValueError("MATLAB_Input has no assessment rows.")

# MATLAB line 361 calls canonicalizeComponentNames (lines 599-619).
# Read each component name, recognize its spelling, and write the standard name. Standardizes Spelling
for row_index in input_table.index:
    component_name = input_table.loc[row_index, "Component"]

    # Split into words and join them with one space to remove extra whitespace.
    words = component_name.split()
    component_name = " ".join(words)
    lowercase_name = component_name.lower()

    if lowercase_name in ["concept", "design concept"]:
        component_name = "Concept"

    elif lowercase_name == "design verification":
        component_name = "Design Verification"

    elif lowercase_name == "manufacturing":
        component_name = "Manufacturing"

    elif lowercase_name in [
        "integration",
        "assembly & integration",
        "assembly/integration",
        "assembly and integration",
    ]:
        component_name = "Assembly and Integration"

    elif lowercase_name in [
        "implementation verification",
        "impl. verification",
        "impl verification",
    ]:
        component_name = "Impl. Verification"

    elif lowercase_name in ["operational setup", "operation setup"]:
        component_name = "Operation Setup"

    elif lowercase_name in ["operational execution", "operation execution"]:
        component_name = "Operation Execution"

    input_table.loc[row_index, "Component"] = component_name

# MATLAB lines 362-367: uppercase Cat and validate row labels/categories.
input_table["Cat"] = input_table["Cat"].str.upper()
for column in ["Branch", "Component", "Indicator"]:
    if (input_table[column] == "").any():
        raise ValueError(f"Every assessment row needs {column}.")
if not input_table["Cat"].isin(["T", "O"]).all():
    raise ValueError("Cat must be T or O on every assessment row.")

# Only the explicit status 'Unable to assess' excludes a row (ignoring case).
# MATLAB lines 368-374: mark unassessed rows and require their Z cells blank.
input_table["Unassessed"] = False
if "Status" in input_table.columns:
    status = input_table["Status"].str.lower()
    input_table["Unassessed"] = status == "unable to assess"
score_is_filled = input_table["Z"] != ""
unassessed_row_has_score = input_table["Unassessed"] & score_is_filled
if unassessed_row_has_score.any():
    raise ValueError("Rows marked Unable to assess must have blank Z. Clear the score explicitly.")
# MATLAB line 375: toNumericColumn converts scores (helper at lines 591-597).
input_table["Z"] = pd.to_numeric(input_table["Z"], errors="coerce")


# %% 12. Turns individual indicator scores into one assessment profile for each component and rater
# MATLAB line 78 calls buildProfiles (defined at lines 378-428).
# Average T and O separately for each person and component.
# MATLAB lines 379-381: require all components and reject unknown names.
# Coverage checking uses validateComponentCoverage (lines 621-629).
for component in component_order:
    if not (input_table["Component"] == component).any():
        raise ValueError(f"Missing required component: {component}")
if not input_table["Component"].isin(component_order).all():
    raise ValueError("MATLAB_Input contains an unknown Component.")
# MATLAB lines 390-391: require a nonblank rater ID for every assessment row.
if (input_table["RaterID"] == "").any():
    raise ValueError("RaterID must be filled on every assessment row.")

# MATLAB lines 382-383: expectedBranches, aligned with componentOrder.
expected_branches = ["Design", "Design", "Implementation", "Implementation", "Implementation", "Operation", "Operation",]
# Check the assessments before calculating the profile averages.
# MATLAB lines 384-388: each component must belong to its expected branch.
for component_index in range(len(component_order)):
    component = component_order[component_index]
    expected_branch = expected_branches[component_index]
    component_rows = input_table.loc[input_table["Component"] == component]

    for branch in component_rows["Branch"]:
        if branch.lower() != expected_branch.lower():
            raise ValueError(f"Wrong Branch for component {component}.")

# MATLAB lines 406-408: a rater cannot assess the same indicator twice, checks if there is repitition
# within the same component. Compare indicator names in lowercase.
assessment_names = input_table[["Component", "RaterID", "Indicator"]].copy()
assessment_names["Indicator"] = assessment_names["Indicator"].str.lower()
duplicate_rows = assessment_names.duplicated()
if duplicate_rows.any():
    duplicate = input_table.loc[duplicate_rows].iloc[0]
    component = duplicate["Component"]
    rater_id = duplicate["RaterID"]
    raise ValueError(f"Duplicate indicator within {component} / {rater_id}.")

# MATLAB lines 409-419: warn about unassessed rows and check usable scores.
excluded_rows = input_table.loc[input_table["Unassessed"] == True]
if not excluded_rows.empty:
    excel_rows = excluded_rows["SourceRow"].tolist()
    warnings.warn(f"Excluded unassessed indicators at Excel rows {excel_rows}.")

scored_input = input_table.loc[input_table["Unassessed"] == False]
bad_rows = []
for row_index in scored_input.index:
    score = scored_input.loc[row_index, "Z"]
    if not np.isfinite(score) or score < 0 or score > 4:
        excel_row = int(scored_input.loc[row_index, "SourceRow"])
        bad_rows.append(excel_row)

if len(bad_rows) > 0:
    raise ValueError(f"Invalid Z at Excel rows {bad_rows}. Scores must be between 0 and 4.")

# Build one summary row (technical score and organizational score) for each component and rater. MATLAB lines 394-424.
profile_rows = []
# Read the component and its branch from the same position in their lists.
for component_index in range(len(component_order)):
    component = component_order[component_index]
    branch = expected_branches[component_index]
    component_rows = input_table.loc[input_table["Component"] == component]

    # groupby gives us one person's ID and all their assessment rows at a time.
    # sort=False keeps raters in their original worksheet order.
    for rater_id, rater_rows in component_rows.groupby("RaterID", sort=False):
        # Leave out assessments marked Unable to assess.
        scored_rows = rater_rows.loc[rater_rows["Unassessed"] == False]

        # Get the technical and organizational scores separately.
        technical_scores = scored_rows.loc[scored_rows["Cat"] == "T", "Z"]
        organizational_scores = scored_rows.loc[scored_rows["Cat"] == "O", "Z"]
        if technical_scores.empty or organizational_scores.empty:
            raise ValueError(f"{component} / {rater_id} needs at least one T and one O score.")

        mean_technical_score = technical_scores.mean()
        mean_organizational_score = organizational_scores.mean()

        # Save the two averages and the number of rows used.
        profile = {
            "Branch": branch,
            "Component": component,
            "RaterID": rater_id,
            "Z_T": mean_technical_score,
            "Z_O": mean_organizational_score,
            "NInputRows": len(rater_rows),
            "NUsedRows": len(scored_rows),
            "NExcludedRows": len(rater_rows) - len(scored_rows),
        }
        profile_rows.append(profile)

# MATLAB line 78: the completed table is called raterTable.
rater_table = pd.DataFrame(profile_rows)


# %% 13. converts each rater profile’s average scores into three model parameters (base mean success probability, multiplier, beta-distribution strength) using the mappings defined in section 4
# MATLAB lines 80-84: calculate parameters from scores, not Excel formulas.
# Work through one component/rater profile at a time.
# .loc[row_index, "column"] reads or writes one cell in the table.
for row_index in rater_table.index:
    technical_score = rater_table.loc[row_index, "Z_T"]
    organizational_score = rater_table.loc[row_index, "Z_O"]

    # MATLAB line 82: find the base success probability from the technical score.
    # np.interp finds the value between the score levels, like MATLAB interp1.
    # Example: score 2.5 gives (0.75 + 0.88) / 2 = 0.815.
    base_success_probability = np.interp(technical_score, score_levels, mu_t_levels)

    # MATLAB lines 83-84: find the multiplier and strength from the O score.
    organizational_multiplier = np.interp(organizational_score, score_levels, m_o_levels)
    base_strength = np.interp(organizational_score, score_levels, s_o_levels)

    # Save these values using the same column names as MATLAB.
    rater_table.loc[row_index, "mu_T"] = base_success_probability
    rater_table.loc[row_index, "m_O"] = organizational_multiplier
    rater_table.loc[row_index, "s_O"] = base_strength


# %% 14. Calculate the Beta distribution for each rater profile
# These distributions describe component SUCCESS probability p.
# Failure probability will later be calculated as q = 1 - p.

for row_index in rater_table.index:
    base_success_probability = rater_table.loc[row_index, "mu_T"]
    organizational_multiplier = rater_table.loc[row_index, "m_O"]
    base_strength = rater_table.loc[row_index, "s_O"]

    # MATLAB line 85: multiply the base mean by the organizational multiplier.
    mean_success_probability = base_success_probability * organizational_multiplier

    # Keep the mean between 0.01 and 0.99, just as MATLAB does.
    if mean_success_probability < 0.01:
        mean_success_probability = 0.01
    elif mean_success_probability > 0.99:
        mean_success_probability = 0.99

    # MATLAB line 88: adjust the strength for the lifecycle phase.
    # At a fixed mean, a larger strength gives a narrower Beta distribution.
    strength = base_strength * lambda_phase

    # MATLAB lines 89-90: calculate the two Beta parameters.
    mean_failure_probability = 1 - mean_success_probability
    alpha = mean_success_probability * strength
    beta = mean_failure_probability * strength

    # Save this profile's calculated values in the table.
    rater_table.loc[row_index, "mu"] = mean_success_probability
    rater_table.loc[row_index, "strength"] = strength
    rater_table.loc[row_index, "alpha_p"] = alpha
    rater_table.loc[row_index, "beta_p"] = beta

# %% 15. Display the calculated parameters
# MATLAB lines 94-97 print phase, test settings, and the profile count.
# Displaying the parameter table is added so we can inspect this step.
print(f"Lifecycle phase: {phase_name} -> lambda = {lambda_phase:.2f}")
print(f"Test evidence: n = {n_test}, k_fail = {k_fail}, q_req = {q_req:.3f}")
print(f"Assessment rows: {len(input_table)}; component/rater profiles: {len(rater_table)}")

parameter_columns = ["Component", "RaterID", "Z_T", "Z_O", "mu_T", "m_O", "s_O", "mu", "strength", "alpha_p", "beta_p",]
parameter_table = rater_table[parameter_columns]
print(parameter_table.to_string(index=False))

# %% 16. combines the rater distributions for each component and generates its prior Monte Carlo samples, before using test evidence.
# MATLAB lines 99-158. Each column holds one component's failure probabilities.
# Each row represents one possible combination of component probabilities.
#ombines the rater distributions for each component and generates that component’s prior probability samples
number_of_components = len(component_order)
q = np.zeros((n_prior, number_of_components))
pool_summary_rows = []

for component_index in range(number_of_components):
    # 1. Get the profiles for this component.
    component = component_order[component_index]
    belongs_to_component = rater_table["Component"] == component
    component_profiles = rater_table.loc[belongs_to_component]
    number_of_profiles = len(component_profiles)

    if number_of_profiles == 0:
        raise ValueError(f"Component {component} has no usable assessments.")

    # 2. Give each profile equal weight. MATLAB lines 116-117.
    profile_weight = 1 / number_of_profiles
    weights = np.full(number_of_profiles, profile_weight)
    rater_table.loc[belongs_to_component, "WeightWithinComponent"] = profile_weight

    # Use arrays so multiplication is element by element, like MATLAB .*.
    means = component_profiles["mu"].to_numpy()
    alphas = component_profiles["alpha_p"].to_numpy()
    betas = component_profiles["beta_p"].to_numpy()

    # 3. Calculate the pool mean and variance. MATLAB lines 122-128.
    # With equal weights, a weighted average is just the ordinary mean.
    strengths = alphas + betas
    variance_denominator = strengths**2 * (strengths + 1)
    profile_variances = alphas * betas / variance_denominator

    pool_mean = np.mean(means)
    within_rater_variance = np.mean(profile_variances)
    differences_from_pool_mean = means - pool_mean
    between_rater_variance = np.mean(differences_from_pool_mean**2)
    pool_variance = within_rater_variance + between_rater_variance

    # 4. Calculate a single Beta approximation. MATLAB lines 130-139.
    # We will sample the original mixture, not this approximation.
    moment_matched_strength = pool_mean * (1 - pool_mean) / pool_variance - 1
    if moment_matched_strength > 0:
        moment_matched_alpha = pool_mean * moment_matched_strength
        moment_matched_beta = (1 - pool_mean) * moment_matched_strength
    else:
        moment_matched_strength = np.nan
        moment_matched_alpha = np.nan
        moment_matched_beta = np.nan

    # 5. Select a profile for each sample, then draw its success probability.
    # MATLAB lines 143-150. Profile positions start at zero in Python.
    selected_profiles = rng.choice(number_of_profiles, size=n_prior, replace=True, p=weights)
    success_samples = np.zeros(n_prior)

    for profile_index in range(number_of_profiles):
        uses_this_profile = selected_profiles == profile_index
        number_of_draws = np.count_nonzero(uses_this_profile)
        if number_of_draws > 0:
            alpha = alphas[profile_index]
            beta = betas[profile_index]
            draws = rng.beta(alpha, beta, size=number_of_draws)
            success_samples[uses_this_profile] = draws

    # MATLAB line 151: convert success probabilities into failure probabilities.
    q[:, component_index] = 1 - success_samples

    # 6. Save this component's summary. MATLAB lines 153-158.
    component_summary = {
        "BasicEvent": basic_event_order[component_index],
        "Branch": component_profiles.iloc[0]["Branch"],
        "Component": component,
        "NProfiles": number_of_profiles,
        "PoolMeanP": pool_mean,
        "WithinRaterVariance": within_rater_variance,
        "BetweenRaterVariance": between_rater_variance,
        "PoolVariance": pool_variance,
        "MomentMatchedStrength": moment_matched_strength,
        "MomentMatchedAlpha": moment_matched_alpha,
        "MomentMatchedBeta": moment_matched_beta,
        "MeanZT": component_profiles["Z_T"].mean(),
        "MeanZO": component_profiles["Z_O"].mean(),
    }
    pool_summary_rows.append(component_summary)

pool_summary = pd.DataFrame(pool_summary_rows)
print("\nComponent pool summary:")
print(pool_summary.to_string(index=False))


# %% 17. Calculate the branch and top-event failure probabilities
# MATLAB line 169 calls faultTreeNodes, defined at lines 480-488.
# q[:, 0] means all sample rows from the first component column.
q_concept = q[:, 0]
q_design_verification = q[:, 1]
q_manufacturing = q[:, 2]
q_integration = q[:, 3]
q_implementation_verification = q[:, 4]
q_operation_setup = q[:, 5]
q_operation_execution = q[:, 6]

# An OR gate fails if any of its inputs fail:
# failure probability = 1 - probability that all inputs succeed.
q_design = 1 - (1 - q_concept) * (1 - q_design_verification)
q_implementation = 1 - (1 - q_manufacturing) * (1 - q_integration) * (1 - q_implementation_verification)
q_operation = 1 - (1 - q_operation_setup) * (1 - q_operation_execution)
q_top = 1 - (1 - q_design) * (1 - q_implementation) * (1 - q_operation)

# MATLAB lines 171-175: std(..., ddof=0) matches MATLAB std(..., 1).
print("\nPrior branch and top-event results:")
print(f"q_dsgn: mean = {np.mean(q_design):.6f}, std = {np.std(q_design, ddof=0):.6f}")
print(f"q_impl: mean = {np.mean(q_implementation):.6f}, std = {np.std(q_implementation, ddof=0):.6f}")
print(f"q_op:   mean = {np.mean(q_operation):.6f}, std = {np.std(q_operation, ddof=0):.6f}")
print(f"q_top:  mean = {np.mean(q_top):.6f}, std = {np.std(q_top, ddof=0):.6f}")


# %% 18. updates the prior samples using the observed test results, producing posterior samples.
# MATLAB lines 177-191 and posteriorWeights at lines 438-448.
# The likelihood is q_top**k_fail * (1 - q_top)**(n_test - k_fail).
# Calculate it directly here, rather than using MATLAB's logarithmic form.
if not np.isfinite(q_top).all() or (q_top < 0).any() or (q_top > 1).any():
    raise ValueError("Failure-probability samples must be finite and within [0, 1].")

number_of_successes = n_test - k_fail
likelihood = q_top**k_fail * (1 - q_top)**number_of_successes
total_likelihood = np.sum(likelihood)

# With many tests, direct likelihoods can become too small to represent.
if not np.isfinite(total_likelihood) or total_likelihood <= 0:
    raise ValueError("Likelihoods are zero or invalid. Cannot calculate posterior weights.")

posterior_weights = likelihood / total_likelihood

effective_sample_size = 1 / np.sum(posterior_weights**2)
print(f"\nPosterior effective sample size: {effective_sample_size:.1f} of {n_prior}")
if effective_sample_size < 0.01 * n_prior:
    warnings.warn("Posterior effective sample size is low. Increase n_prior.")

# Select whole rows so the components and branches stay paired with q_top.
posterior_indices = rng.choice(n_prior, size=n_posterior, replace=True, p=posterior_weights)
q_posterior = q[posterior_indices, :]
q_design_posterior = q_design[posterior_indices]
q_implementation_posterior = q_implementation[posterior_indices]
q_operation_posterior = q_operation[posterior_indices]
q_top_posterior = q_top[posterior_indices]


# %% 19. summarizes the prior and posterior samples for all 11 fault-tree nodes: seven components, three branches, and the top event. for the terminal output
# MATLAB lines 193-199 and buildNodeSummary at lines 490-515.
node_names = basic_event_order + ["q_dsgn", "q_impl", "q_op", "q_top"]
prior_nodes = np.column_stack((q, q_design, q_implementation, q_operation, q_top))
posterior_nodes = np.column_stack((q_posterior, q_design_posterior, q_implementation_posterior, q_operation_posterior, q_top_posterior,))
node_summary_rows = []
for node_index in range(len(node_names)):
    # 1. Get this node's name and its prior and posterior samples.
    node_name = node_names[node_index]
    prior_samples = prior_nodes[:, node_index]
    posterior_samples = posterior_nodes[:, node_index]

    # 2. Calculate requirement probabilities only for the top event.
    # np.nan leaves the other nodes' requirement results blank.
    prior_exceeds = np.nan
    posterior_exceeds = np.nan
    if node_name == "q_top":
        prior_exceeds = np.mean(prior_samples > q_req)
        posterior_exceeds = np.mean(posterior_samples > q_req)

    # 3. Build one summary row. Keys are column names; values are results.
    # method="hazen" matches MATLAB's percentile convention.
    summary_row = {
        "Node": node_name,
        "PriorNSamples": len(prior_samples),
        "PostNSamples": len(posterior_samples),
        "PriorMean": np.mean(prior_samples),
        "PriorStd": np.std(prior_samples, ddof=0),
        "PriorMedian": np.median(prior_samples),
        "PriorP025": np.percentile(prior_samples, 2.5, method="hazen"),
        "PriorP95": np.percentile(prior_samples, 95, method="hazen"),
        "PriorP975": np.percentile(prior_samples, 97.5, method="hazen"),
        "PriorPexc": prior_exceeds,
        "PriorPmeet": 1 - prior_exceeds,
        "PostMean": np.mean(posterior_samples),
        "PostStd": np.std(posterior_samples, ddof=0),
        "PostMedian": np.median(posterior_samples),
        "PostP025": np.percentile(posterior_samples, 2.5, method="hazen"),
        "PostP95": np.percentile(posterior_samples, 95, method="hazen"),
        "PostP975": np.percentile(posterior_samples, 97.5, method="hazen"),
        "PostPexc": posterior_exceeds,
        "PostPmeet": 1 - posterior_exceeds,
    }
    node_summary_rows.append(summary_row)

# Combine the dictionaries into a table with one row per node.
node_summary = pd.DataFrame(node_summary_rows)

print("\nPrior and posterior summary:")
print(node_summary.to_string(index=False))


# %% 20. Compare pooling distributions with averaging scores
# MATLAB lines 201-223 and sampleLegacyComponentFailures at lines 456-478.
# This second method averages the retained profile scores within each component
# before building one Beta distribution. It is a separate comparison run.
q_legacy = np.zeros((n_prior, number_of_components))

# 1. Average the scores and calculate one Beta distribution per component.
for component_index in range(number_of_components):
    component = component_order[component_index]
    component_profiles = rater_table.loc[rater_table["Component"] == component]

    mean_technical_score = component_profiles["Z_T"].mean()
    mean_organizational_score = component_profiles["Z_O"].mean()

    base_success_probability = np.interp(mean_technical_score, score_levels, mu_t_levels)
    organizational_multiplier = np.interp(mean_organizational_score, score_levels, m_o_levels)
    base_strength = np.interp(mean_organizational_score, score_levels, s_o_levels)

    mean_success_probability = base_success_probability * organizational_multiplier
    if mean_success_probability < 0.01:
        mean_success_probability = 0.01
    elif mean_success_probability > 0.99:
        mean_success_probability = 0.99

    strength = base_strength * lambda_phase
    alpha = mean_success_probability * strength
    mean_failure_probability = 1 - mean_success_probability
    beta = mean_failure_probability * strength

    # Draw success probabilities, then convert them to failure probabilities.
    success_samples = rng.beta(alpha, beta, size=n_prior)
    q_legacy[:, component_index] = 1 - success_samples

# 2. Apply the same fault-tree equations as section 17.
q_design_legacy = 1 - (1 - q_legacy[:, 0]) * (1 - q_legacy[:, 1])
q_implementation_legacy = 1 - ((1 - q_legacy[:, 2]) * (1 - q_legacy[:, 3]) * (1 - q_legacy[:, 4]))
q_operation_legacy = 1 - (1 - q_legacy[:, 5]) * (1 - q_legacy[:, 6])
q_top_legacy = 1 - ((1 - q_design_legacy) * (1 - q_implementation_legacy) * (1 - q_operation_legacy))

# 3. Calculate the likelihood and weights directly, just as in section 18.
legacy_likelihood = q_top_legacy**k_fail * (1 - q_top_legacy)**number_of_successes
total_legacy_likelihood = np.sum(legacy_likelihood)

# Direct likelihoods can round to zero when the number of tests is large.
if not np.isfinite(total_legacy_likelihood) or total_legacy_likelihood <= 0:
    raise ValueError("Comparison likelihoods are zero or invalid. Cannot calculate posterior weights.")

legacy_weights = legacy_likelihood / total_legacy_likelihood

# 4. Resample the comparison top-event probabilities using these weights.
legacy_posterior_indices = rng.choice(n_prior, size=n_posterior, replace=True, p=legacy_weights)
q_top_legacy_posterior = q_top_legacy[legacy_posterior_indices]

# 5. Save one dictionary row for each method's statistics.
methods = ["Scores averaged across profiles", "Exact equal-weight linear pool"]
comparison_priors = [q_top_legacy, q_top]
comparison_posteriors = [q_top_legacy_posterior, q_top_posterior]
comparison_rows = []

for method_index in range(len(methods)):
    prior_samples = comparison_priors[method_index]
    posterior_samples = comparison_posteriors[method_index]
    comparison_row = {
        "Method": methods[method_index],
        "PriorMean": np.mean(prior_samples),
        "PriorStd": np.std(prior_samples, ddof=0),
        "PriorP95": np.percentile(prior_samples, 95, method="hazen"),
        "PostMean": np.mean(posterior_samples),
        "PostP95": np.percentile(posterior_samples, 95, method="hazen"),
    }
    comparison_rows.append(comparison_row)

pooling_comparison = pd.DataFrame(comparison_rows)
print("\nTop-event method comparison:")
print(pooling_comparison.to_string(index=False))


# %% 21. creates the output folders and plots the success-probability distributions for each component.
# MATLAB lines 33-37: create a new folder for this run. Do not overwrite a run.
output_root.mkdir(exist_ok=True)
run_dir.mkdir(exist_ok=False)
figures_dir.mkdir()

# MATLAB lines 160-162 call plotComponentPool (lines 517-547).
# We draw these figures here, after all analysis calculations are finished.
# The horizontal axis is SUCCESS probability p, not failure probability q.
success_grid = np.linspace(0.001, 0.999, 1500)

for component_index in range(number_of_components):
    # 1. Get this component's rater profiles and pool summary.
    component = component_order[component_index]
    component_profiles = rater_table.loc[rater_table["Component"] == component]
    pool_results = pool_summary.iloc[component_index]

    # 2. Create an empty plot and start the combined density at zero.
    # figure is the whole picture; axes is the plotting area inside it.
    figure, axes = plt.subplots()
    pool_density = np.zeros(len(success_grid))

    # 3. Draw each rater's curve and add their contribution to the pool.
    # MATLAB lines 524-528.
    for row_index in component_profiles.index:

        profile = component_profiles.loc[row_index]
        rater_id = profile["RaterID"]
        alpha = profile["alpha_p"]
        beta = profile["beta_p"]
        weight = profile["WeightWithinComponent"]

        # Evaluate the Beta density at the plotting points in success_grid.
        rater_density = beta_distribution.pdf(success_grid, alpha, beta)
        axes.plot(success_grid, rater_density, label=rater_id)

        weighted_density = weight * rater_density
        pool_density = pool_density + weighted_density

    # 4. Draw the combined distribution. MATLAB lines 531-532.
    axes.plot(success_grid, pool_density, label="Exact equal-weight linear pool",)

    # 5. Draw the single-Beta approximation. MATLAB 533-535.
    approximate_alpha = pool_results["MomentMatchedAlpha"]
    approximate_beta = pool_results["MomentMatchedBeta"]
    if np.isfinite(approximate_alpha) and np.isfinite(approximate_beta):
        approximate_density = beta_distribution.pdf(success_grid, approximate_alpha, approximate_beta)
        axes.plot(success_grid, approximate_density, label="Moment-matched Beta (approx.)",)

    # 6. Mark the mean and label the plot. MATLAB lines 538-543.
    pool_mean = pool_results["PoolMeanP"]
    pool_variance = pool_results["PoolVariance"]
    axes.axvline(pool_mean, label="Pool mean")
    axes.set_xlabel("Readiness probability p")
    axes.set_ylabel("Probability density")
    axes.set_title(f"{component}: mean = {pool_mean:.3f}, variance = {pool_variance:.4f}")
    axes.legend()
    figure.tight_layout()

    # 7. Make the filename from the standard component name.
    # Example: "Design Verification" becomes "pool_design_verification".
    safe_component_name = component.lower()
    safe_component_name = safe_component_name.replace(".", "")
    safe_component_name = safe_component_name.replace(" ", "_")
    figure_name = "pool_" + safe_component_name

    # 8. Save both copies and close this plot before starting the next one.
    # MATLAB saveFigureCopies (645-654); SVG replaces MATLAB's FIG format.
    png_file = figures_dir / f"{figure_name}.png"
    svg_file = figures_dir / f"{figure_name}.svg"
    figure.savefig(png_file)
    figure.savefig(svg_file)
    plt.close(figure)


# %% 22. creates and saves five plots of the overall system’s failure probability, q_top
# MATLAB lines 225-294. density=True gives a probability density histogram.
# Repeat the plotting steps explicitly so each figure is easy to follow.

# MATLAB lines 226-231: prior top-event failure probability.
figure, axes = plt.subplots()
axes.hist(q_top, density=True)
axes.set_xlabel(r"$q_{top}$")
axes.set_ylabel("pdf")
axes.set_title(f"Prior of $q_{{top}}$ (N={n_prior})")
figure.tight_layout()
figure.savefig(figures_dir / "01_prior_q_top.png")
figure.savefig(figures_dir / "01_prior_q_top.svg")
plt.close(figure)

# MATLAB lines 233-238: posterior top-event failure probability.
figure, axes = plt.subplots()
axes.hist(q_top_posterior, density=True)
axes.set_xlabel(r"$q_{top}$")
axes.set_ylabel("pdf")
axes.set_title(f"Posterior $q_{{top}}$ (k={k_fail}, n={n_test})")
figure.tight_layout()
figure.savefig(figures_dir / "02_posterior_q_top.png")
figure.savefig(figures_dir / "02_posterior_q_top.svg")
plt.close(figure)

# MATLAB lines 240-253: prior and posterior on the same axes.
figure, axes = plt.subplots()
axes.hist([q_top, q_top_posterior], density=True, label=["Prior", "Posterior"])
axes.set_xlabel(r"$q_{top}$")
axes.set_ylabel("pdf (MC approximation)")
axes.set_title(f"Prior and Posterior of $q_{{top}}$: k={k_fail} out of n={n_test}")
axes.legend()
figure.tight_layout()
figure.savefig(figures_dir / "03_prior_vs_posterior.png")
figure.savefig(figures_dir / "03_prior_vs_posterior.svg")
plt.close(figure)

# MATLAB lines 255-264: normalize the likelihood over a plotting grid.
# This curve shows the test evidence alone; it is not the posterior density.
failure_grid = np.linspace(0, 1, 2000)
grid_likelihood = failure_grid**k_fail * (1 - failure_grid)**number_of_successes
likelihood_area = np.trapezoid(grid_likelihood, failure_grid)
if not np.isfinite(likelihood_area) or likelihood_area <= 0:
    raise ValueError("Plotting likelihoods are zero or invalid. Cannot normalize the curve.")
likelihood_density = grid_likelihood / likelihood_area

# MATLAB lines 266-282: overlay the normalized likelihood curve.
figure, axes = plt.subplots()
axes.hist([q_top, q_top_posterior], density=True, label=["Prior", "Posterior"])
axes.plot(failure_grid, likelihood_density, label=f"Normalized likelihood (k={k_fail}, n={n_test})")
axes.set_xlabel(r"$q_{top}$")
axes.set_ylabel("pdf / normalized likelihood")
axes.set_title(f"Prior, Posterior, and Likelihood: k={k_fail} out of n={n_test}")
axes.legend()
figure.tight_layout()
figure.savefig(figures_dir / "04_prior_posterior_likelihood.png")
figure.savefig(figures_dir / "04_prior_posterior_likelihood.svg")
plt.close(figure)

# MATLAB lines 284-295: compare the two prior pooling methods.
figure, axes = plt.subplots()
axes.hist([q_top_legacy, q_top], density=True, label=["Scores averaged across profiles", "Exact equal-weight linear pool"],)
axes.set_xlabel(r"$q_{top}$")
axes.set_ylabel("pdf")
axes.set_title("Score aggregation and exact linear pool")
axes.legend()
figure.tight_layout()
figure.savefig(figures_dir / "05_legacy_vs_exact_pool.png")
figure.savefig(figures_dir / "05_legacy_vs_exact_pool.svg")
plt.close(figure)


# %% 23. Save the result tables and run settings
# MATLAB lines 297-316: describe the inputs, settings, and assessment counts.
# This dictionary holds the values for one row of the RunInfo worksheet.
run_information = {
    "RunStamp": run_stamp,
    "InputFile": str(input_file),
    "OutputFolder": str(run_dir),
    "N": n_prior,
    "Mpost": n_posterior,
    "n_test": n_test,
    "k_fail": k_fail,
    "q_req": q_req,
    "phase_name": phase_name,
    "lambda_phase": float(lambda_phase),
    "InputMode": "linear_pool",
    "InputSheet": input_sheet,
    "PoolingMethod": "exact_equal_weight_linear_pool",
    "EffectiveSampleSize": float(effective_sample_size),
    "ModelVersion": "13",
    "Seed": random_seed,
    "ScoreLevels": json.dumps(score_levels.tolist()),
    "MuTLevels": json.dumps(mu_t_levels.tolist()),
    "MOLevels": json.dumps(m_o_levels.tolist()),
    "SOLevels": json.dumps(s_o_levels.tolist()),
    "PhaseLevels": ",".join(phase_levels),
    "LambdaLevels": json.dumps(lambda_levels.tolist()),
    "MeanClipMin": 0.01,
    "MeanClipMax": 0.99,
    "PoolingWeights": "equal_within_component",
    "NInputRows": len(input_table),
    "NUsedRows": int(rater_table["NUsedRows"].sum()),
    "NExcludedRows": int(rater_table["NExcludedRows"].sum()),
    "NRaters": int(rater_table["RaterID"].nunique()),
    "NProfiles": len(rater_table),
    "Implementation": "Python",
    "FigureFormats": "PNG,SVG",
}
run_info = pd.DataFrame([run_information])

# MATLAB lines 318-322: save each table to its own worksheet in results.xlsx.
# The with block closes the workbook after the last worksheet is written.
with pd.ExcelWriter(tables_file, engine="openpyxl") as workbook:
    run_info.to_excel(workbook, sheet_name="RunInfo", index=False)
    rater_table.to_excel(workbook, sheet_name="RaterParameters", index=False)
    pool_summary.to_excel(workbook, sheet_name="PoolSummary", index=False)
    node_summary.to_excel(workbook, sheet_name="NodeSummary", index=False)
    pooling_comparison.to_excel(workbook, sheet_name="PoolingComparison", index=False)

# MATLAB line 325: save the same run information as a JSON text file.
metadata_file = run_dir / "run_metadata.json"
metadata_text = json.dumps(run_information, indent=2, allow_nan=False)
metadata_file.write_text(metadata_text + "\n", encoding="utf-8")

# MATLAB line 336: report the folder containing this run's results.
print(f"\nSaved figures, tables, and run settings to:\n{run_dir}")
