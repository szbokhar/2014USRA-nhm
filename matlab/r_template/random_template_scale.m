function [rankings, placed, placed_cut] = random_template_scale(fname, pcount, off_x, off_y, scales)

    % Load image and get data
    raw_image = imread(fname);
    [~, stack] = gendata(fname);
    [~, ~, stack_depth] = size(stack);

    % Ask user for box
    imshow(raw_image);
    box_coords = ginput();
    x1 = box_coords(1,1);
    y1 = box_coords(1,2);
    x2 = box_coords(2,1);
    y2 = box_coords(2,2);
    box_width = x2-x1;
    box_height = y2-y1;
    hold on;

    % Generate random feature vector
    pts = zeros(pcount,2);
    for i=1:pcount
        pts(i,:) = [rand rand];
    end

    bpts(:,1) = 1+pts(:,1)*(box_width-2);
    bpts(:,2) = 1+pts(:,2)*(box_height-2);

    base = zeros(pcount,stack_depth);

    for i = 1:pcount
        x = x1 + int32(bpts(i,1));
        y = y1 + int32(bpts(i,2));
        base(i,:) = stack(y,x,:);
        plot(x, y, '.y')
    end
    waitforbuttonpress;

    i = 1;
    allScores = [];
    for pwr = scales
        % Pass window over image
        swidth = pwr*box_width;
        sheight = pwr*box_height;
        [tScores, maxtscore] = useTemplate(pts, base, stack, swidth, sheight, off_x, off_y);
        tScores = exp(-(tScores.*tScores)/((maxtscore/10)^2));
        allScores(:,:,i) = tScores;
        i = i+1;

        fprintf('Scale %d\n', pwr);
    end

    lmax = allScores==localmax(allScores, 2, 2, 2);
    bestPoints = lmax.*allScores;
    bestPoints(bestPoints < 0.1) = 0;

    [rankings, placed] = buildRankings(raw_image, bestPoints, box_width, box_height, off_x, off_y, scales);
    displayTemplateMatches(raw_image, rankings, placed, box_width, box_height);
    waitforbuttonpress;
    placed_cut = placed;
    [c, v] = hist(placed(:,4), max(length(placed)/10, 1));
    for j = fliplr(2:(length(c)-1))
        if (c(j-1) > c(j) && c(j+1) > c(j))
            fprintf('Cutting at %d', v(j));
            placed_cut = placed(placed(:,4) > v(j),:);
            break;
        end
    end
    displayTemplateMatches(raw_image, rankings, placed_cut, box_width, box_height);
end


% Pass template over image
function [tScores maxtscore] = useTemplate(pts, base, stack, box_width, box_height, off_x, off_y)
    [pcount dims] = size(pts);
    [image_height image_width stack_depth] = size(stack);
    maxtscore = pcount*stack_depth;

    tScores = maxtscore*ones(int32(image_height/off_y), int32(image_width/off_x));
    [res_h, res_w] = size(tScores);
    bpts(:,1) = 1+pts(:,1)*(box_width-2);
    bpts(:,2) = 1+pts(:,2)*(box_height-2);

    for j=1:res_h
        for i=1:res_w
            x1 = int32(off_x*i-box_width/2);
            y1 = int32(off_y*j-box_height/2);
            if (x1 > 0 && y1 > 0 && x1+box_width <= image_width && y1+box_height <= image_height)
                new = [];
                for k = 1:pcount
                    x = x1 + int32(bpts(k,1));
                    y = y1 + int32(bpts(k,2));
                    new(k,:) = stack(y,x,:);
                end
                diff = new-base;
                diff = diff.*diff;
                tScores(j,i) = sum(diff(:));
            end
        end
        fprintf('=');
    end

end

% Find good responses to template
function [bestPoints tScoresNew] = getBestPoints(tScores, maxtscore)
    tScoresNew = exp(-(tScores.*tScores)/((maxtscore/10)^2));
    lmax = tScoresNew==localmax(tScoresNew, 2, 2);
    bestPoints = lmax.*tScoresNew;
    bestPoints(bestPoints < 0.1) = 0;
end

function [ rankings, placed ] = buildRankings(raw_image, bestPoints, box_width, box_height, off_x, off_y, scales)
    bestSpots = [];
    i = 1;
    for scale = scales
        [tr tc tv] = find(bestPoints(:,:,i));
        ts = scale*ones(size(tr));
        bestSpots = [bestSpots; tv tc tr ts];
        i = i+1;
    end

    placed = [];
    i = 0;
    rankings = fliplr(sortrows(bestSpots, 1)');
    for p = rankings
        if (p(1) < 0.88)
            break
        end
        x1 = p(2)*off_x;
        y1 = p(3)*off_y;
        sca = p(4);

        hit = 1;
        for q = placed'
            hit = hit && (abs(x1-q(1)) > q(3)*box_width/2 || abs(y1-q(2)) > q(3)*box_height/2);
            hit = hit && (abs(x1-q(1)) > sca*box_width/2 || abs(y1-q(2)) > sca*box_height/2);
        end

        if (hit)
            placed = [placed; x1, y1, sca, p(1)];
        end

        i = i+1;
    end

end

function displayTemplateMatches(raw_image, rankings, placed, box_width, box_height)
    hold off;
    imshow(raw_image);
    hold on;

    i = 0;
    placed
    for p = placed'
        sca = p(3);
        x1 = p(1);
        y1 = p(2);
        plot(p(1), p(2), 'oy');
        rectangle('position', [x1-(sca*box_width/2), y1-(sca*box_height/2), sca*box_width, sca*box_height], 'EdgeColor', 'g');
        i = i+1;

        fprintf('Score: %f      X: %d       Y: %d   S: %d\n', p(4), p(1), p(2), p(3));
    end
    hold off;
end

% Local max function
function minA = localmax(A, w, h, d)
    [ height width depth ] = size(A);

    minA = ones(size(A));
    for y = 1:height
        for x = 1:width
            for z=1:depth
                neighbourhood = A(max(y-h,1):min(y+h, height), max(x-w,1):min(x+w, width), max(z-d,1):min(z+d,depth));
                minA(y,x,z) = max(neighbourhood(:));
            end
        end
    end
end

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
    fcount = 11;

    % Setup storage to response to filters
    count = 1;
    responses{fcount} = ones(size(img(:,:,1)));

    % Run filters
    for j=1:1
        for i=1:3
            neww = imfilter(lab(:,:,j),gfilters{i});
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
end
