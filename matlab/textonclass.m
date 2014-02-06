function newimg = texton(fname, box)
    % Load image
    img = imread(fname);

    % Generate sample data for image
    [evalset,stack] = gendata(fname);
    [img_height img_width fcount] = size(stack);

    % Build training data based on clicks
    imshow(img);

    % Background sample clicks
    clicks = ginput();
    [n d] = size(clicks);
    bs = [];
    for i = 1:n
        bx = round(clicks(i,1));
        by = round(clicks(i,2));
        if (by-box>0 && bx-box>0 && by+box<img_height && bx+box<img_width)
            bsample = stack((by-box):(by+box),(bx-box):(bx+box),:);
            temp = reshape(bsample,(box*2+1)^2,fcount);
            bs = [bs; temp];
            sample = img((by-box):(by+box),(bx-box):(bx+box),:);
            newname = strcat('back', num2str(i), '.jpg');
            imwrite(sample, newname)
            disp('bclick');
        end
    end

    % Foreground sample clicks
    clicks = ginput();
    [n d] = size(clicks);
    fs = [];
    for i = 1:n
        fx = round(clicks(i,1));
        fy = round(clicks(i,2));
        if (by-box>0 && bx-box>0 && by+box<img_height && bx+box<img_width)
            fsample = stack((fy-box):(fy+box),(fx-box):(fx+box),:);
            temp = reshape(fsample,(box*2+1)^2,fcount);
            fs = [fs; temp];
            sample = img((fy-box):(fy+box),(fx-box):(fx+box),:);
            newname = strcat('front', num2str(i), '.jpg');
            imwrite(sample, newname)
            disp('fclick');
        end
    end

    % Label sample points for learning
    bs(:,fcount+1) = 1;
    fs(:,fcount+1) = 2;
    data = [bs;fs];

    % Train logistic regression
    disp('Training logistic classifier')
    model = mnrfit(data(:,1:fcount), data(:,fcount+1));

    % Classify all points
    [h w] = size(stack(:,:,2));
    newimg = zeros([h w]);
    classed = mnrval(model, evalset);

    newimg(:) = classed(:,1);
