function blurs = siftdetect(fname)
    img = imread(fname);
    lab = applycform(img, makecform('srgb2lab'));
    L = double(lab(:,:,1))/255;
    a = double(lab(:,:,2))/255;
    b = double(lab(:,:,3))/255;

    blurs = [];

    initSig = 0.5;
    rounds = 10
    for i=0:rounds
        kern = fspecial('gaussian', 31, initSig*2^(i/2));
        blurred = imfilter(L, kern);
        blurs(:,:,i+1) = blurred;
    end

    dog = [];
    for i=1:(rounds-1)
        dog(:,:,i) = blurs(:,:,i) - blurs(:,:,i+1);
        dog = dog/(2*max(dog(:)) - 2*min(dog(:)))+0.5;
        imshow(dog(:,:,i));
        waitforbuttonpress;
    end
end
