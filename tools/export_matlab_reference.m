% Run unchanged native v13, then export draws solely for deterministic parity.
% Usage from the research folder:
% run('lv-readiness/tools/export_matlab_reference.m')
run(fullfile(fileparts(fileparts(fileparts(mfilename('fullpath')))), 'mc_faulttree_bayes_demo_v13.m'));
referencePrior = [q qDsgn qImpl qOp qTop];
referencePosterior = [qPost qDsgnPost qImplPost qOpPost qTopPost];
save(fullfile(runDir, 'joint_samples.mat'), 'referencePrior', 'referencePosterior', ...
    'postWeights', 'postIndex', 'qTopLegacy', 'qTopLegacyPost', '-v7');
matlabEnvironment = struct('Version', version, 'Computer', computer, 'Toolboxes', ver);
referenceFid = fopen(fullfile(runDir, 'matlab_environment.json'), 'w', 'n', 'UTF-8');
assert(referenceFid ~= -1, 'Unable to save MATLAB environment metadata');
fprintf(referenceFid, '%s\n', jsonencode(matlabEnvironment));
fclose(referenceFid);
fprintf('REFERENCE_RUN=%s\n', runDir);
close all;
