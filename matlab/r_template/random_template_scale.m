function bestPoints = random_template_with_corr(fname, pcount, off_x, off_y)
    raw_image = imread(fname);
    [data stack] = gendata(fname);
    [image_height image_width stack_depth] = size(stack);

    imshow(raw_image);
    box_coords = ginput();
    x1 = box_coords(1,1);
    y1 = box_coords(1,2);
    x2 = box_coords(2,1);
    y2 = box_coords(2,2);
    box_width = x2-x1;
    box_height = y2-y1;

    pts = [];
    for i=1:pcount
        pts(i,:) = [rand rand];
    end

    pts(:,1) = 1+pts(:,1)*(box_width-2);
    pts(:,2) = 1+pts(:,2)*(box_height-2);

    base = [];

    for i = 1:pcount
        x = x1 + int32(pts(i,1));
        y = y1 + int32(pts(i,2));
        base(i,:) = stack(y,x,:);
    end

    maxtscore = pcount*stack_depth;

    tScores = maxtscore*ones(int32(image_height/off_y), int32(image_width/off_x));
    [res_h, res_w] = size(tScores);

    for j=1:res_h
        for i=1:res_w
            x1 = int32(off_x*i-box_width/2);
            y1 = int32(off_y*j-box_height/2);
            if (x1 > 0 && y1 > 0 && x1+box_width <= image_width && y1+box_height <= image_height)
                new = [];
                for k = 1:pcount
                    x = x1 + int32(pts(k,1));
                    y = y1 + int32(pts(k,2));
                    new(k,:) = stack(y,x,:);
                end
                diff = new-base;
                diff = diff.*diff;
                tScores(j,i) = sum(diff(:));
            end
        end
        fprintf('Row done');
    end

    tScores = exp(-(tScores.*tScores)/((maxtscore/10)^2));
    lmax = tScores==localmax(tScores, 1, 1);
    bestPoints = lmax.*tScores;
    bestPoints(bestPoints < 0.1) = 0;
    imshow(raw_image);
    hold on;

    [r c v] = find(bestPoints);
    scores = [v r c];

    i = 0;
    for p = fliplr(sortrows(scores, 1)')
        fprintf('Score: %f      X: %d       Y: %d\n', p(1), p(2), p(3));
        plot(p(3)*off_y, p(2)*off_x, 'or')
        i = i+1;
        if (mod(i,10) == 0)
            waitforbuttonpress;
        end
    end

function minA = localmax(A, w, h)
    [ height width ] = size(A);

    minA = ones(size(A));
    for y = 1:height
        for x = 1:width
            neighbourhood = A(max(y-h,1):min(y+h, height), max(x-w,1):min(x+w, width));
            minA(y,x) = max(neighbourhood(:));
        end
    end
