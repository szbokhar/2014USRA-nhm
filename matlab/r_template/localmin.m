function minA = localmin(A, w, h)
    [ height width ] = size(A);

    minA = ones(size(A));
    for y = 1:height
        for x = 1:width
            neighbourhood = A(max(y-h,1):min(y+h, height), max(x-w,1):min(x+w, width));
            minA(y,x) = min(neighbourhood(:));
        end
    end
