/**
 * User Controller 
 */

const bcrypt = require('bcrypt');

const {generateToken,JWT_EXPIRY} = require('../middleware/auth');

//In-memory user store (replace with DB in production)
const users= new Map();

//Environment configs
const ADMIN_EMAIL=process.env.ADMIN_EMAIL;
const ADMIN_PASSWORD=process.env.ADMIN_PASSWORD;

/**
 * Normalize email to lowercase and trim whitespace
 */

const normalizeEmail=(email)=>
{
    return String(email).toLowerCase().trim();
};

/**
 * Intialize admin user if credentials are provided
 */

const initializeAdmin = async () => {
  try {
    if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
      console.warn('Admin credentials not provided in .env');
      return;
    }

    const email = normalizeEmail(ADMIN_EMAIL);

    if (users.has(email)) return;

    const hashedPassword = await bcrypt.hash(ADMIN_PASSWORD, 10);

    users.set(email, {
      email,
      password: hashedPassword,
      name: 'Admin User',
      role: 'admin',
      createdAt: new Date().toISOString()
    });

    console.log(`Admin user initialized: ${email}`);
  } catch (err) {
    console.error('Failed to initialize admin:', err.message);
  }
};

//INitialize only in non-production OR if explicitly allowed in production
if (process.env.NODE_ENV !== 'production' || process.env.INIT_ADMIN === 'true') {
  initializeAdmin();
}
/**
 * Validate email format 
 */

const isValidEmail=(email)=>{
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Register a new user
 */

const register=async (req,res)=>{
    try{
        let {email,password,name}=req.body;
        if(!email || !password){
            return res.status(400).json({
                success:false,
                error:'Email and password are required',
                Message:'Please provide both email and password to register'
            });
        }
        
        email=normalizeEmail(email);    

        //Email format validation
        if(!isValidEmail(email)){
            return res.status(400).json({
                success:false,
                error:'Invalid email format',
                Message:'Please provide a valid email address'
            });
        }
        //password strength validation
        if(password.length < 6){
            return res.status(400).json({
                success:false,
                error:'Weak password',
                Message:'Password must be at least 8 characters long'
            });
        }

        if(users.has(email)){
            return res.status(409).json({
                success:false,
                error:'User already exists',
                Message:'A user with this email already exists. Please login or use a different email to register'
            });
        }
        
        const hashedPassword=await bcrypt.hash(password,10);
        const user={
            email,
            password:hashedPassword,
            name:name?.trim() || email.spilt('@')[0],
            role:'user',
            createdAt:new Date().toISOString()
        };
        users.set(email,user);

        const token=generateToken({
            email:user.email,
            name:user.name,
            role:user.role
        },JWT_EXPIRY);
        
        res.status(201).json({
            success:true,
            message:'User registered successfully',
            data:{
                user:{
                    email:user.email,
                    name:user.name,
                    role:user.role,
                },
                token,
                expiresIn:JWT_EXPIRY
            }
        });
    } catch (err) {
        console.error('Error during user registration:', err.message);
        res.status(500).json({
            success:false,
            error:'Internal server error',
            message:'An error occurred while registering the user'
        });
    }
};

//Login existing user

const login=async (req,res)=>{
    try{
        let {email,password}=req.body;
        if(!email || !password){
            return res.status(400).json({
                success:false,
                error:'Email and password are required',
                Message:'Please provide both email and password to login'
            });
        }

        email=normalizeEmail(email);

        const user=users.get(email);
        if(!user){
            return res.status(401).json({
                success:false,
                error:'Invalid credentials',
                Message:'No user found with this email. Please register first'
            });
        }

        const isPasswordValid=await bcrypt.compare(password,user.password);
        if(!isPasswordValid){
            return res.status(401).json({
                success:false,
                error:'Invalid credentials',
                Message:'Incorrect password. Please try again'
            });
        }
        
        const token=generateToken({
            email:user.email,
            name:user.name,
            role:user.role
        },JWT_EXPIRY);


        res.status(200).json({
            success:true,
            message:'User logged in successfully',
            data:{
                user:{
                    email:user.email,
                    name:user.name,
                    role:user.role
                },
                token,
                expiresIn:JWT_EXPIRY
            }
        });
    } catch (err) {
        console.error('Error during user login:', err.message);
        res.status(500).json({
            success:false,
            error:'Internal server error',
            message:'An error occurred while logging in the user'
        });
    }
};

/**
 * Get current authenticated user info
 */

const getProfile=(req,res)=>{
    try{
        const {user}=req.auth;
        res.status(200).json({
            success:true,
            data:{
                email:user.email,
                name:user.name,
                role:user.role,
                createdAt:user.createdAt
            }
        }); 
    }catch (err) {
        console.error('Error fetching user profile:', err.message);
        res.status(500).json({
            success:false,
            error:'Internal server error',
            message:'An error occurred while fetching the user profile'
        });
    }
}

/**
 * REfresh JWT token (optional, can be used to extend session without re-login)
 */
const refreshToken=(req,res)=>{
    try{
        const {user}=req.auth;
        const token=generateToken({
            email:user.email,
            name:user.name,
            role:user.role
        },JWT_EXPIRY);

        res.status(200).json({
            success:true,
            message:'Token refreshed successfully',
            data:{
                token,
                expiresIn:JWT_EXPIRY
            }
        });
    }catch (err) {
        console.error('Error refreshing token:', err.message);
        res.status(500).json({
            success:false,
            error:'Internal server error',
            message:'An error occurred while refreshing the token'
        });
    }   
}


/**
 * Logout user (for JWT, this is typically handled client-side by deleting the token, but we can implement token blacklisting if needed)
 */

const logout=(req,res)=>{
    return res.status(200).json({
        success:true,
        message:'User logged out successfully. Please delete the token on the client side to complete logout'
    });
};

module.exports={
    register,
    login,
    getProfile,
    refreshToken,
    logout
};
