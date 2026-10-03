% Export native MATLAB v13 draws for the optional Python parity check.
% The native script stays outside this repository. Set referenceScript before
% running this wrapper if it is not in the parent research folder:
% referenceScript = 'C:/research/mc_faulttree_bayes_demo_v13.m';
% run('tools/export_matlab_reference.m');

% Locate and run the native calculation. Its own variables supply the arrays below.
if ~exist('referenceScript', 'var')
    researchFolder = fileparts(fileparts(fileparts(mfilename('fullpath'))));
    referenceScript = fullfile(researchFolder, 'mc_faulttree_bayes_demo_v13.m');
end
assert(isfile(referenceScript), 'Set referenceScript to the native MATLAB v13 file.');
run(referenceScript);

% Preserve full rows: seven basic events followed by four fault-tree nodes.
% Saving weights and indices lets Python replay exactly the same posterior rows.
referencePrior = [q qDsgn qImpl qOp qTop];
referencePosterior = [qPost qDsgnPost qImplPost qOpPost qTopPost];
save(fullfile(runDir, 'joint_samples.mat'), 'referencePrior', 'referencePosterior', ...
    'postWeights', 'postIndex', 'qTopLegacy', 'qTopLegacyPost', '-v7');

% Record the MATLAB environment alongside the sample file for traceability.
matlabEnvironment = struct('Version', version, 'Computer', computer, 'Toolboxes', ver);
referenceFid = fopen(fullfile(runDir, 'matlab_environment.json'), 'w', 'n', 'UTF-8');
assert(referenceFid ~= -1, 'Unable to save MATLAB environment metadata');
fprintf(referenceFid, '%s\n', jsonencode(matlabEnvironment));
fclose(referenceFid);
fprintf('REFERENCE_RUN=%s\n', runDir);
close all;
