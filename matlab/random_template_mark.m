function bestPoints = random_template_with_corr(fname, pcount, off_x, off_y)

    % Load image and get data
    raw_image = imread(fname);
    [data stack] = gendata(fname);
    [image_height image_width stack_depth] = size(stack);

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
        plot(x, y, '.y')
    end
    waitforbuttonpress;

    % Pass window over image
    [tScores maxtscore] = useTemplate(pts, base, stack, box_width, box_height, off_x, off_y);
    [bestPoints tScores] = getBestPoints(tScores, maxtscore);
    hold off;
    imshow(tScores);
    waitforbuttonpress;

    % Display responses
    displayTemplateMatches(raw_image, bestPoints, box_width, box_height, off_x, off_y);
end


% Pass template over image
function [tScores maxtscore] = useTemplate(pts, base, stack, box_width, box_height, off_x, off_y)
    [pcount dims] = size(pts);
    [image_height image_width stack_depth] = size(stack);
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

function displayTemplateMatches(raw_image, bestPoints, box_width, box_height, off_x, off_y)
    imshow(raw_image);
    hold on;
    [r c v] = find(bestPoints);
    scores = [v c r];
    placed = [];
    i = 0;
    for p = fliplr(sortrows(scores, 1)')
        fprintf('Score: %f      X: %d       Y: %d\n', p(1), p(2), p(3));
        x1 = p(2)*off_x;
        y1 = p(3)*off_y;

        hit = 1;
        for q = placed'
            hit = hit && (abs(x1-q(1)) > box_width/2 || abs(y1-q(2)) > box_height/2);
        end

        if (hit)
            plot(x1, y1, 'or')
            rectangle('position', [x1-(box_width/2), y1-(box_height/2), box_width, box_height], 'EdgeColor', 'b');
            placed = [placed; x1, y1];
        end

        i = i+1;
        if (mod(i,10) == 0)
            waitforbuttonpress;
        end
    end
end

% Local max function
function minA = localmax(A, w, h)
    [ height width ] = size(A);

    minA = ones(size(A));
    for y = 1:height
        for x = 1:width
            neighbourhood = A(max(y-h,1):min(y+h, height), max(x-w,1):min(x+w, width));
            minA(y,x) = max(neighbourhood(:));
        end
    end
end
