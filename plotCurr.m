fileName = '/var/data/ocl/currentVsTime/cVsT_nplc0.1-new.csv';
%fileName = '/var/data/ocl/currentVsTime/cVsT_nplc10-new.csv';
%fileName = '/var/data/ocl/currentVsTime/cVsT_nplc1-new.csv';

data = csvread(fileName);
time = data(:,1);
current = data(:,2);

%smooth01 = smoothdata(current,'movmean',0.1,'SamplePoints',time);
smooth1 = smoothdata(current,'movmean',1,'SamplePoints',time);
%smooth10 = smoothdata(current,'movmean',10,'SamplePoints',time);

%v=15;
%current_f = conv(current,ones(v,1)/v,'same');

figure
%plot(time,smooth01*1e9,time,smooth1*1e9,time,smooth10*1e9)
plot(time,smooth1*1e9)
%legend('raw','my-smooth','current-f')
xlabel ('Time [s]')
ylabel ('Current [nA]')
grid on
