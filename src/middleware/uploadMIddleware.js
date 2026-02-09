const multer=require('multer');
const path=require('path');
const fs=require('fs');

const uploadPath=process.env.UPLOAD_DIR || './uploads';
//Ensure upload directory exists
if(!fs.existsSync(uploadPath)){
    fs.mkdirSync(uploadPath,{recursive:true});
}

//Configure multer storage
const storage=multer.diskStorage({
    destination:(req,file,cb)=>{
        cb(null,uploadPath);
    },
    filename:(req,file,cb)=>{
        //Generate unique filename:timestamp-randomstring-originalname
        const uniqueSuffix=Date.now()+'-'+Math.round(Math.random()*1E9);
        const extension=path.extname(file.originalname);
        const nameWithoutExt=path.basename(file.originalname,extension);
        cb(null,`${nameWithoutExt}-${uniqueSuffix}${extension}`);
    }
});

//File filter to validate file types
const fileFilter=(req,file,cb)=>{
    const allowedTypes=process.env.ALLOWED_FILE_TYPES.split(',').map(type=>type.trim()).filter(Boolean);
    if(allowedTypes.includes(file.mimetype)){
        cb(null,true);
    } else {
        cb(new Error(`File type ${file.mimetype} not allowed.Allowed types are: ${allowedTypes.join(', ')}`),false);
    }

};

//configure multer upload
const upload=multer({
    storage:storage,
    fileFilter:fileFilter,
    limits:{
        fileSize:parseInt(process.env.MAX_FILE_SIZE) || 1024*1024*5  //default 5MB
    }
});

module.exports=upload;