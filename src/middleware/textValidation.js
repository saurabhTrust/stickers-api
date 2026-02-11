/**
 * validated the text input for text-based sticker generation
 */

const validateTextInput = (req, res, next) => {
    const { text,keywords } = req.body;

    //must provide either text or keywords

    if(!text && !keywords){
        return res.status(400).json({
            success:false,
            error:'Either text or keywords must be provided'
        });
    }
    //If text is provided, validate it
    if(text){
        if(typeof text!=='string' ||text.trim().length===0){
            return res.status(400).json({
                success:false,
                error:'Text must be a non-empty string'
            });
        }
        //Length validation
        if(text.length<1 || text.length>200){
            return res.status(400).json({
                success:false,
                error:'Text must be between 1 and 200 characters'
            });
        }

        //sanitize the text(remove special characters that could cause issues)
        req.body.text=text.trim();
    }

    //If keywords are provided, validate them
    if(keywords){
        if(!Array.isArray(keywords) || keywords.length===0){
            return res.status(400).json({
                success:false,
                error:'Keywords must be a non-empty array'
            });
        }
        //Maximum 10 keywords allowed
        if(keywords.length>10){
            return res.status(400).json({
                success:false,
                error:'A maximum of 10 keywords are allowed'
            });
        }
        //Validate each keyword
        for(let i=0;i<keywords.length;i++){
            const keyword=keywords[i];

            if(typeof keyword!=='string' || keyword.trim().length===0){
                return res.status(400).json({
                    success:false,
                    error:`Keyword at index ${i} must be a non-empty string`
                });
            }
            if(keyword.length<1 || keyword.length>50){
                return res.status(400).json({
                    success:false,
                    error:`Keyword at index ${i} must be between 1 and 50 characters`
                });
            }
        }
        //Sanitize keywords
        req.body.keywords=keywords.map(k=>k.trim().toLowerCase());
    }
    next();
};
module.exports=validateTextInput;