//Global error handler
const multer=require('multer');
const errorHandler=(err,req,res,next)=>{
    console.error('Error:',err);

    //multer file upload errors
    if(err instanceof multer.MulterError){
        if(err.code==='LIMIT_FILE_SIZE'){
            return res.status(413).json({
                success:false,
                error:`File too large. Max allowed size is ${process.env.MAX_FILE_SIZE} bytes`,
                maxsize:process.env.MAX_FILE_SIZE
            });
        }

        return res.status(400).json({
            success:false,
            error:err.message
        });
    }

    //Custom errors from validation middleware
    if(err.message.includes('Invalid file type')){
        return res.status(400).json({
            success:false,
            error:err.message
        });
    }
    //Default to 500 server error
    res.status(500).json({
        success:false,
        error:'Internal server error',
        message:process.env.NODE_ENV==='development' ? err.message : undefined
    });
};
module.exports=errorHandler;