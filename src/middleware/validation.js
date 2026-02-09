const sharp=require('sharp');
const fs=require('fs').promises;

//validate image after upload
const validateImage=async(req,res,next)=>{
    try{
        if(!req.file){
            return res.status(400).json({
                success:false,
                error:'No file uploaded'
            });
        }
        const filePath=req.file.path;
        //use sharp to validate the image
        const metadata=await sharp(filePath).metadata();
        //check dimensions
        const maxWidth=4096;
        const maxHeight=4096;
        const minWidth=100;
        const minHeight=100;

        if(metadata.width>maxWidth || metadata.height>maxHeight){
            //clean the uploaded file
            await fs.unlink(filePath);
            return res.status(400).json({
                success:false,
                error:`Imagdimensions too large. Max allowed is ${maxWidth}x${maxHeight}px`
            });
        }
        if(metadata.width<minWidth || metadata.height<minHeight){
            //clean the uploaded file
            await fs.unlink(filePath);
            return res.status(400).json({
                success:false,
                error:`Image dimensions too small. Min allowed is ${minWidth}x${minHeight}px`
            });
        }
        //Attach metadata to request object for further processing
        req.imageMetadata={
            width:metadata.width,
            height:metadata.height,
            format:metadata.format,
            size:req.file.size
        };
        next();
    }
    catch(error){
        //If sharp throws an error, it means the file is not a valid image
        if(req.file && req.file.path){
            await fs.unlink(req.file.path).catch(()=>{});
        }
        return res.status(400).json({
            success:false,
            error:'Invalid or corrupted image file'
        });
    }  
};

module.exports=validateImage;


