function newimg = texton(fname, box, pcount, slides_y, slides_x)
    % Load image
    img = imread(fname);

    % Generate sample data for image
    [evalset,stack] = gendata(fname);
    [img_height img_width fcount] = size(stack);

    % Build training data based on clicks
    imshow(img);

    % Background sample clicks
    disp('Click on background points');
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
    disp('Click on foreground points');
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


    % Build template
    disp('Select one bug');
    box_coords = ginput();
    x1 = box_coords(1,1);
    y1 = box_coords(1,2);
    x2 = box_coords(2,1);
    y2 = box_coords(2,2);
    box_width = x2-x1
    box_height = y2-y1

    pts = [];
    for i=1:pcount
        pts(i,:) = [rand rand];
    end

    tmp(:,1) = 1+pts(:,1)*(box_width-2);
    tmp(:,2) = 1+pts(:,2)*(box_height-2);

    base = [];

    for i = 1:pcount
        x = x1 + int32(tmp(i,1));
        y = y1 + int32(tmp(i,2));
        base(i,:) = stack(y,x,:);
    end


    % Iterate through each connected component in binary mask
    bin_blur = imfilter(newimg<0.5, fspecial('gaussian', 5, 1))>0.5;
    [labeled, count] = bwlabel(bin_blur);
    boxes = zeros(count,6);

    % Get rectangular bounding box for connected component
    for i = 1:count
        [r,c] = find(labeled==i);
        x1 = min(c);
        x2 = max(c);
        y1 = min(r);
        y2 = max(r);
        h = y2-y1;
        w = x2-x1;
        boxes(i,:) = [x1,y1,x2,y2,w,h];
    end

    % Save each bounding box as a seprate image
    [r,c] = size(boxes);
    for i = 1:r
        b = boxes(i,:);
        subimg = img(b(2):b(4),b(1):b(3),:);

        swidth = b(3)-b(1);
        sheight = b(4)-b(2);

        if (swidth > 20 && sheight > 20)
            sample = stack(b(2):b(4),b(1):b(3),:);
            tmp(:,1) = 1+pts(:,1)*(swidth-2);
            tmp(:,2) = 1+pts(:,2)*(sheight-2);
            new = [];
            for i = 1:pcount
                x = b(1)+int32(tmp(i,1));
                y = b(2)+int32(tmp(i,2));
                new(i,:) = stack(y,x,:);
            end
            i;
            diff = new-base;
            diff = diff.*diff;
            diff = sum(diff(:));

            newname = strcat('part', num2str(diff), '-', num2str(i), '.jpg');
            imwrite(subimg, newname);
            disp(strcat('Writing file',' ', newname));
        end
    end
