function boxes = selectTwoPoints(fname, tolerance, r0,r1)
    % Load image and prompt for two clicks
    img = imread(fname);
    imshow(img);

    % Get positions of clicks
    clicks = ginput();
    posBack = round(clicks(1,:));
    posFront = round(clicks(2,:));
    bx = posBack(1);
    by = posBack(2);
    fx = posFront(1);
    fy = posFront(2);
    close all;

    % Make a new grayscale image the size of the input image
    [h,w,c] = size(img);
    newimg = zeros(h,w);

    for y = 1:h
        for x = 1:w
            newimg(y,x) = 0.21*img(y,x,1) + 0.71*img(y,x,2) + 0.07*img(y,x,3);
        end
    end

    % Blur new image
    blur = fspecial('gaussian',2,2);
    newimg = imfilter(newimg,blur);

    % Find the background colour based onf first click
    backCol = newimg((by-30):(by+30), (bx-30):(bx+30), :);
    backCol = mean(mean(backCol));

    % Subtract background colour from image
    newimg = abs(newimg - backCol);

    % Determine good threshold value based on both clicks
    bgray = newimg(by,bx);
    fgray = newimg(fy,fx);
    mid = (bgray+fgray)/2;

    % Make binary image
    newimg(newimg < mid) = 0;
    newimg(newimg > mid) = 1;

    % Process image to remove noise
    % newimg = bwmorph(newimg,'erode',ones(tolerance));
    % newimg = bwmorph(newimg,'dilate',ones(tolerance));
    % newimg = bwmorph(newimg,'dilate',ones(tolerance));

    % Iterate through each connected component in binary mask
    [labeled, count] = bwlabel(newimg);
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

    % Filter out bounding boxes that are too small or big
    [h,w,c] = size(img);
    rows = find(boxes(:,5)>2*tolerance & boxes(:,6)>2*tolerance & boxes(:,5)<w/4 & boxes(:,6)<h/4);
    boxes = boxes(rows,:);

    % Save each bounding box as a seprate image
    [r,c] = size(boxes);
    for i = r0:min(r1,r)
        b = boxes(i,:);
        subimg = img(b(2):b(4),b(1):b(3),:);
        newname = strcat('part', num2str(i), '-', fname);
        imwrite(subimg, newname);
        disp(strcat('Writing file',' ', newname));
    end
