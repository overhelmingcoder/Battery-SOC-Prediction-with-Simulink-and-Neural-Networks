% Code to plot soc_estimation_example inputs, which are current,
% voltage, and temperature.

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
if ~exist('figHandleInputs', 'var') || ~isgraphics(figHandleInputs, 'figure')
    figHandleInputs=figure('Name','BatterySOCSimulinkEstimation_inputs');
end
figure(figHandleInputs);
clf(figHandleInputs);
set(figHandleInputs, 'Position', [15,   60,   770,   480]);


subplot(3,1,1)
plot(out.inputSignals.time,out.inputSignals.signals(1,1).values)
title('Input current');
xlabel('Time');
ylabel('A');
grid on
subplot(3,1,2)
plot(out.inputSignals.time,out.inputSignals.signals(1,2).values)
title('Input voltage');
xlabel('Time');
ylabel('V');
subplot(3,1,3)
plot(out.inputSignals.time,out.inputSignals.signals(1,3).values)
title('Input temperature');
xlabel('Time');