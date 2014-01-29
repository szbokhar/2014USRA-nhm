function newimg = texton(fname, box)
    % Load image and prompt for two clicks
    img = imread(fname);

    [evalset,stack] = gendata(fname);
    [z z fcount] = size(stack);

    % Get positions of clicks
    imshow(img);
    clicks = ginput();
    [n d] = size(clicks);

    bs = [];
    for i = 1:n
        bx = round(clicks(i,1));
        by = round(clicks(i,2));
        bsample = stack((by-box):(by+box),(bx-box):(bx+box),:);
        temp = reshape(bsample,(box*2+1)^2,fcount);
        bs = [bs; temp];
        disp('bclick');
    end

    clicks = ginput();
    [n d] = size(clicks);

    fs = [];
    for i = 1:n
        fx = round(clicks(i,1));
        fy = round(clicks(i,2));
        fsample = stack((fy-box):(fy+box),(fx-box):(fx+box),:);
        temp = reshape(fsample,(box*2+1)^2,fcount);
        fs = [fs; temp];
        disp('fclick');
    end

    bs(:,fcount+1) = 1;
    fs(:,fcount+1) = 2;
    data = [bs;fs];

    % Train svm
    disp('Training logistic classifier')
    model = mnrfit(data(:,1:fcount), data(:,fcount+1));

    % Classify all points
    [h w] = size(stack(:,:,1));
    newimg = zeros([h w]);
    classed = mnrval(model, evalset);

    newimg(:) = classed(:,1);
    imshow(newimg);



