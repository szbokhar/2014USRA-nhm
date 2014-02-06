function newimg = texton(fname, box)
    % Load image
    img = imread(fname);

    % Generate sample data for image
    [evalset,stack] = gendata(fname);
    [z z fcount] = size(stack);

    bimages = dir('back*');
    [count z] = size(bimages);
    bs = [];
    for i = 1:count
        fname = bimages(i).name;
        [dat, ~] = gendata(fname);
        bs = [bs;dat];
        disp(fname);
    end

    fimages = dir('front*');
    [count z] = size(bimages);
    for i = 1:count
        fname = fimages(i).name;
        [dat, ~] = gendata(fname);
        fs = [bs;dat];
        disp(fname);
    end


    % Label sample points for learning
    bs(:,fcount+1) = 1;
    fs(:,fcount+1) = 2;
    data = [bs;fs];
    size(data)

    % Train logistic regression
    disp('Training logistic classifier')
    model = mnrfit(data(:,1:fcount), data(:,fcount+1));

    % Classify all points
    [h w] = size(stack(:,:,2));
    newimg = zeros([h w]);
    classed = mnrval(model, evalset);

    newimg(:) = classed(:,1);
