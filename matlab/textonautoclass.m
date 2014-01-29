function newimg = textonautoclass(fname)
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
    cvt = makecform('srgb2lab');
    lab = applycform(img, cvt);
    lab = double(lab);

    gfilters = {k_g1, k_g2, k_g3};
    lfilters = {k_g1L, k_g2L, k_g3L, k_g4L};
    xyfilters = {k_g3X, k_g4X, k_g3Y, k_g4Y};
    fcount = 17;

    % Setup storage to response to filters
    count = 1;
    responses{fcount+1} = ones(size(img(:,:,1)));

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
    for i=1:4
        neww = imfilter(lab(:,:,1),lfilters{i});
        responses{count} = neww;
        count = count+1;
    end
    for i=1:4
        neww = imfilter(lab(:,:,1),xyfilters{i});
        responses{count} = neww;
        count = count+1;
    end

    % Store responses in HxWx18 dimentional array
    stack(:,:,1) = responses{1};

    for i = 2:(fcount+1)
        stack(:,:,i) = responses{i};
    end

    % Get positions of clicks
    imshow(img);
    clicks = ginput();
    [n d] = size(clicks);

    bs = [];
    for i = 1:n
        bx = round(clicks(i,1));
        by = round(clicks(i,2));
        bsample = stack((by-box):(by+box),(bx-box):(bx+box),:);
        temp = reshape(bsample,(box*2+1)^2,fcount+1);
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
        temp = reshape(fsample,(box*2+1)^2,fcount+1);
        fs = [fs; temp];
        disp('fclick');
    end

    bs(:,fcount+2) = 0;
    fs(:,fcount+2) = 1;
    data = [bs;fs]

    % Train svm
    disp('Training SVM')
    machine = svmtrain(data(:,1:(fcount+1)), data(:,fcount+2), 'method','QP');

    % Classify all points
    [h w] = size(img(:,:,1));
    newimg = zeros([h w]);

    for y = 1:h
        for x = 1:w
            sample = reshape(stack(y,x,:),1,fcount+1);
            class = svmclassify(machine,sample);
            newimg(y,x) = class;
        end
        disp(strcat('Row', num2str(y)));
    end

