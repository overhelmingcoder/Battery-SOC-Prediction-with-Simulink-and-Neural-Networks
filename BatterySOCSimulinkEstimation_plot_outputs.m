% Code to plot soc_estimation_example outputs, which are the truth, network
% estimation, and EKF estimation.

% Copyright 2021 The MathWorks, Inc.
%% Setup
model = 'BatterySOCSimulinkEstimation';

if ~strcmp(bdroot, model)
    load_system(model);
    set_param(0, 'CurrentSystem', model);
end

%% Generate data for figure
if ~exist('out', 'var')
    out = sim(model);
end

%% Create figures
if ~exist('figHandleOutputs', 'var') || ~isgraphics(figHandleOutputs, 'figure')
    figHandleOutputs=figure('Name','BatterySOCSimulinkEstimation_outputs');
end

figure(figHandleOutputs);
clf(figHandleOutputs);
set(figHandleOutputs, 'Position', [15,   60,   770,   480]);

plot(out.estimationOutput.time,out.estimationOutput.signals(1,1).values)
hold on
plot(out.estimationOutput.time,out.estimationOutput.signals(1,2).values)
legend('true', '<NN>');
title('True VS Network Estimation');
xlabel('Time');
ylabel('SOC');
grid on
hold off