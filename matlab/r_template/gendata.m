function [data, stack] = gendata(fname)
    % Load image and prompt for two clicks
    img = imread(fname);

    % setup texton filters
    lap = fspecial('laplacian');
    grad_x = fspecial('sobel')';
    grad_y = fspecial('sobel');
    k_g1 = fspecial('gaussian', 9, 0.5);
    k_g2 = fspecial('gaussian', 9, 1);
    k_g3 = fspecial('gaussian', 9, 1.5);
    k_g4 = fspecial('gaussian', 9, 2);
    k_g1L = imfilter(k_g1,lap);
    k_g2L = imfilter(k_g2,lap);
    k_g3L = imfilter(k_g3,lap);
    k_g4L = imfilter(k_g4,lap);
    k_g3X = imfilter(k_g3,grad_x);
    k_g4X = imfilter(k_g4,grad_x);
    k_g3Y = imfilter(k_g3,grad_y);
    k_g4Y = imfilter(k_g4,grad_y);
    img = double(img)/255;
    cvt = makecform('srgb2lab');
    lab = applycform(img, cvt);
    lab = double(lab);

    gfilters = {k_g1, k_g2, k_g3};
    lfilters = {k_g1L, k_g2L, k_g3L, k_g4L};
    xyfilters = {k_g3X, k_g4X, k_g3Y, k_g4Y};
    fcount = 9;

    % Setup storage to response to filters
    count = 1;
    responses{fcount} = ones(size(img(:,:,1)));

    % Run filters
    for j=1:3
        for i=1:3
            neww = imfilter(lab(:,:,j),gfilters{i});
            % imshow(neww, [min(neww(:)) max(neww(:))]);
            % waitforbuttonpress
            responses{count} = neww;
            count = count+1;
        end
    end

    % Store responses in HxWx18 dimentional array
    stack(:,:,1) = responses{1};

    for i = 2:(fcount)
        stack(:,:,i) = responses{i};
    end

    [h w d] = size(stack);
    stack = stack(9:(h-9), 9:(w-9),:);
    [h w d] = size(stack);
    data = reshape(stack, h*w, d);

    for i=1:fcount
        low = min(data(:,i));
        high = max(data(:,i));
        data(:,i) = (data(:,i)-low)/(high-low);
        stack(:,:,i) = (stack(:,:,i)-low)/(high-low);
    end