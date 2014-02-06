function pieces = random_template(fname, pcount, slides_y, slides_x)
    raw_image = imread(fname);
    [data stack] = gendata(fname);
    [image_height image_width stack_depth] = size(stack);

    imshow(raw_image);
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

    pts(:,1) = 1+pts(:,1)*(box_width-2);
    pts(:,2) = 1+pts(:,2)*(box_height-2);

    base = [];

    for i = 1:pcount
        x = x1 + int32(pts(i,1));
        y = y1 + int32(pts(i,2));
        base(i,:) = stack(y,x,:);
    end

    pieces = [];
    for dy = slides_y
        row_pieces = [];
        for dx = slides_x
            if (x2+dx < image_width && y2+dy < image_height && x1+dx > 0 && y1+dy > 0)
                new = [];
                for i = 1:pcount
                    x = x1 + dx+int32(pts(i,1));
                    y = y1 + dy+int32(pts(i,2));
                    new(i,:) = stack(y,x,:);
                end
                diff = new-base;
                diff = diff.*diff;
                row_pieces = [row_pieces sum(diff(:))];
            end
        end
        pieces = [pieces; row_pieces];
    end

    low = min(pieces(:))
    high = max(pieces(:))
    pieces = pieces-low;

