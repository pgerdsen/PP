//**************** Javascript Game Development Library *********************
//** Author:  Mike Thomas
//** Date: 10/31/2019
//** Version: 4.0
//**************************************************************************
//** Description
//**    This Library was written to help new programmers create 2D javascript
//**    games easier so they can focus more on their prgram logic and less on
//**    syntax.  Specifically, it takes much of the complexity of collision
//**    detection and Spritesheet management out of the process
//***************************************************************************
//** Revision History
//***************************************************************************

function GameMaster(){
    this.imageDir = ".\\images\\";
    this.soundDir = ".\\sounds\\";
    this.libraryDir = ".\\lib\\";
    this.CurrentScreen = "MainMenu";
    this.debugstr = "";
    this.bgDX = 0;
    this.bgDY = 0;
    this.gameIterator=0;
    this.gameIterate = function(){
        this.gameIterator++;
        //** just in case of an overflow
        if (this.gameIterator < 0){
            this.gameIterate = 0;
        }
    }
    this.moveObjectWithBackground = function(o){
        o.x += this.bgDX;
        o.y += this.bgDY;
        if (o.x < o.useWidth*-1){
            o.x = canvas.width;
        }
        if (o.x > canvas.width){
            o.x = 0-o.useWidth;
        }
    }
    this.debugAppend = function(str){
        this.debugstr = this.debugstr +  str 
    }
    this.debug = function(){
        document.getElementById("debug").innerHTML = this.debugstr;
        this.debugstr = "";
    }
}
function GameText(){
    this.font = "48px Arial";
    this.fillStyle = "Blue";
    this.x = 800;
    this.y = 45;
    this.alpha = 0.5;
    this.draw = function(inText) {
        ctx.font = this.font;
        ctx.fillStyle = this.fillStyle;
        ctx.globalAlpha = this.alpha;
        ctx.fillText(inText, this.x, this.y);
        ctx.globalAlpha = 1.0;
    }
}
// For creating a single image Sprite
function Sprite (x,y,width,height, useWidth, useHeight,image) {
        this.x = x;
        this.y = y;
        this.dX = 0;
        this.dY = 0;
        this.width = width;
        this.height = height;
        this.useWidth = useWidth;
        this.useHeight = useHeight;
        this.image = image;
        this.alpha = 1.0; //transparency of image whe drawn
        this.collision = false;
        this.visible = true;
        this.moveWithBackground = false;
        
        this.draw = function() {
            if (this.visible) {
                if (this.moveWithBackground == true){
                    game.moveObjectWithBackground(this);
                }
                ctx.globalAlpha = this.alpha;
                ctx.drawImage(this.image,0,0,this.width,this.height,this.x,this.y,this.useWidth,this.useHeight);
                ctx.globalAlpha = 1.0;
            }
        }
        this.checkCollisions = function(obj2) {
            if(this.x + this.useWidth > obj2.x && this.x < obj2.x + obj2.useWidth) {
                if (this.y + this.useHeight > obj2.y && this.y < obj2.y + obj2.useHeight){
                this.collision = true;
                    return true;
                }
            }
            return false;
        }
        //This one just checks if "this" moves one more spot down whether its bottom
        //will collide with the passed object
        this.checkBottomCollision = function(obj2) {
            if(this.x + this.useWidth > obj2.x && this.x < obj2.x + obj2.useWidth) {
                if (this.y + this.useHeight + 1 > obj2.y && this.y < obj2.y + obj2.useHeight){
                    this.collision = true;
                    //console.log("setting to true");
                    return true;
                }
            }
            return false;
        }
        //This one just checks if "this" moves one more spot down whether its bottom
        //will collide with the passed object
        this.checkBottomCollision = function(obj2) {
            return BottomCollision(this, obj2);
        }
        //This one just checks if "this" moves one more spot up whether its top
        //will collide with the passed object
        this.checkTopCollision = function(obj2){
            return TopCollision(this,obj2);
       }
        //This one just checks if "this" moves one more spot right whether its right
        //will collide with the passed object
        this.checkRightCollision = function(obj2) {
            return RightCollision(this,obj2);
        }
        //This one just checks if "this" moves one more spot right whether its left
        //will collide with the passed object
        this.checkLeftCollision = function(obj2) {
            return LeftCollision(this,obj2);
        }
    }
// For creating a Sprite that uses a spritesheet for motion
// note - assumes each row represents a direction and each column a frame
function SpriteSheet (x,y,width,height, useWidth, useHeight, dir, frame, image) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.useWidth = useWidth;
        this.useHeight = useHeight;
        this.dX = 0;
        this.dY = 0;
        this.dirMax = dir; //Max number of "directions" the Sprite can move in
        this.currentDir = 0; //start the Sprite with the first "direction"
        this.maxFrame = frame; //Max number of Frames the Sprite animation takes
        this.currentFrame = 0; //start on current Frame
        //this.sheet = image; //deprecated sheet - was inconsistent with other objects
        this.image = image;
        this.alpha = 1.0; //transparency of image whe drawn
        this.collision = false;
        this.visible = true;
        this.moveWithBackground = false;
        this.canJump = false;
        this.gravity = 0; //How fast he falls - should be set for any character that can fall/jump
        this.isJumping = false; // set to true once jump starts and is not set back nutil is "grounded" - this keeps from jumping in mid-air
        this.jumpMax = 40;
        this.jumpCount = 0; // Sets the number of refresh cycles the character can jump - once set to zero (probably by some collision) -  this value is set to zero
        
        this.jump = function(){
            if (this.canJump && this.isJumping == false) {
                this.isJumping = true;
                this.jumpCount = this.jumpMax;
            }
        }
        this.stopJump = function(){
            this.jumpCount = 0;
            myKeys.space = false;
        }
        this.checkJump = function(){
            if (this.isJumping && this.jumpCount > 0){
                this.y -= (this.gravity + 1);
                this.jumpCount --;
            } else{
                this.stopJump();
            }
        }
        this.applyGravity = function(){
            this.y += this.gravity;
        }
        this.draw = function() {
            if (this.visible) {
                ctx.globalAlpha = this.alpha; //This command sets the opacity to half - meaning you can see though any images painted after this
                ctx.drawImage(this.image,this.currentFrame * this.width,this.currentDir * this.height,this.width,this.height,this.x,this.y,this.useWidth,this.useHeight);
                ctx.globalAlpha = 1.0; //Setting the opacity back to 1 - which mean solid
            }
        }
        // Increments the Sprite animation frame.  If already at the max goes back to zero position
        this.advanceFrame = function() {
            this.currentFrame++;
            if (this.currentFrame > this.maxFrame) {
                this.currentFrame = 0;
            }
        }
        // Changes the Sprite "direction" or row of animation - will only change to a valid value
        this.changeDir = function(dir) {
            if (dir <= this.dirMax && dir >= 0) {
                this.currentDir = dir;
            }
        }
        this.checkCollisions = function(obj2) {
            this.collision = false; // assume no collision at first
            if(this.x + this.useWidth > obj2.x && this.x < obj2.x + obj2.useWidth) {
                if (this.y + this.useHeight > obj2.y && this.y < obj2.y + obj2.useHeight){
                    this.collision = true;
                }
            }
            return this.collision;
        }
        //This one just checks if "this" moves one more spot down whether its bottom
        //will collide with the passed object
        this.checkBottomCollision = function(obj2) {
            return BottomCollision(this, obj2);
        }
        //This one just checks if "this" moves one more spot up whether its top
        //will collide with the passed object
        this.checkTopCollision = function(obj2){
            return TopCollision(this,obj2);
       }
        //This one just checks if "this" moves one more spot right whether its right
        //will collide with the passed object
        this.checkRightCollision = function(obj2) {
            return RightCollision(this,obj2);
        }
        //This one just checks if "this" moves one more spot right whether its left
        //will collide with the passed object
        this.checkLeftCollision = function(obj2) {
            return LeftCollision(this,obj2);
        }
    }
    //end of SpriteSheet
//**********************************************************************************************************************************
//********************************** E X P E R I M E N T A L ***********************************************************************
//
// This version it to add in new functionality from the regular Spritesheet.  Specifically, the ability to have each "Frame" to have
// its own size ( Width & Height).  This way, Sprites like Street Figheter where kicks, etc are wider than when they stand can work
//
// For creating a Sprite that uses a spritesheet for motion
// note - assumes each row represents a direction and each column a frame
function imgFrame (x,y,width,height) {
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
}
function SpritePage (x,y,image) {
        this.x = x;
        this.y = y;
        this.dX = 0;
        this.dY = 0;
        this.currentRow = 0; //start the Sprite with the first "direction"
        this.currentFrame = 0; //start on current Frame
        this.image = image;
        this.alpha = 1.0; //transparency of image whe drawn
        this.collision = false;
        this.visible = true;
        //**** Experimental - creating a 2D array of images
        //** 1st Dim is the Row or an action - like move left; move right; attack, etc
        //** second Dim is an individual frame in that action
        //** going to want each frame to be an object as I want it to have attributes
        //** such as width and height
        //** perhaps even things like how often to repain ( for refresh speed)
        //** could create a companion file for the SpriteSheet that signifies all of the
        //** locations and sizes of each row & frame to make it easier to use
        this.frame = [];
    
        this.moveWithBackground = false;
        this.canJump = false;
        this.gravity = 0; //How fast he falls - should be set for any character that can fall/jump
        this.isJumping = false; // set to true once jump starts and is not set back nutil is "grounded" - this keeps from jumping in mid-air
        this.jumpMax = 40;
        this.jumpCount = 0; // Sets the number of refresh cycles the character can jump - once set to zero (probably by some collision) -  this value is set to zero
        
        this.jump = function(){
            if (this.canJump && this.isJumping == false) {
                this.isJumping = true;
                this.jumpCount = this.jumpMax;
            }
        }
        this.stopJump = function(){
            this.jumpCount = 0;
            myKeys.space = false;
        }
        this.checkJump = function(){
            if (this.isJumping && this.jumpCount > 0){
                this.y -= (this.gravity + 1);
                this.jumpCount --;
            } else{
                this.stopJump();
            }
        }
        this.applyGravity = function(){
            this.y += this.gravity;
        }
        this.draw = function() {
            if (this.visible) {
                ctx.globalAlpha = this.alpha; //This command sets the opacity to half - meaning you can see though any images painted after this

                ctx.drawImage(this.image,this.frame[this.currentRow][this.currentFrame].x,
                              this.frame[this.currentRow][this.currentFrame].y,this.frame[this.currentRow][this.currentFrame].width,this.frame[this.currentRow][this.currentFrame].height,this.x,this.y,this.frame[this.currentRow][this.currentFrame].width,this.frame[this.currentRow][this.currentFrame].height);
                ctx.globalAlpha = 1.0; //Setting the opacity back to 1 - which mean solid

            }
        }
        // Increments the Sprite animation frame.  If already at the max goes back to zero position
        this.advanceFrame = function() {
            this.currentFrame++;
            console.log(this.currentFrame);
            if (this.currentFrame >= this.frame[this.currentRow].length) {
                this.currentFrame = 0;
                this.currentRow++;
                if (this.currentRow >= this.frame.length){
                    this.currentRow = 0;
                }
            }
        }
        // Changes the Sprite "direction" or row of animation - will only change to a valid value
        this.changeDir = function(dir) {
            if (dir <= this.dirMax && dir >= 0) {
                this.currentDir = dir;
            }
        }
        this.checkCollisions = function(obj2) {
            this.collision = false; // assume no collision at first
            if(this.x + this.useWidth > obj2.x && this.x < obj2.x + obj2.useWidth) {
                if (this.y + this.useHeight > obj2.y && this.y < obj2.y + obj2.useHeight){
                    this.collision = true;
                }
            }
            return this.collision;
        }
        //This one just checks if "this" moves one more spot down whether its bottom
        //will collide with the passed object
        this.checkBottomCollision = function(obj2) {
            return BottomCollision(this, obj2);
        }
        //This one just checks if "this" moves one more spot up whether its top
        //will collide with the passed object
        this.checkTopCollision = function(obj2){
            return TopCollision(this,obj2);
       }
        //This one just checks if "this" moves one more spot right whether its right
        //will collide with the passed object
        this.checkRightCollision = function(obj2) {
            return RightCollision(this,obj2);
        }
        //This one just checks if "this" moves one more spot right whether its left
        //will collide with the passed object
        this.checkLeftCollision = function(obj2) {
            return LeftCollision(this,obj2);
        }
    }
    //end of SpritePage
    //SpriteArray is when instead of a spritesheet you must create an array of sprites 
    //from seprate images.  At thsi time SpriteArrays only support 1-dimension arrays
    //if you want to use 2dimenstions you'll simply create multiple arrays and change
    //the inArray to a differnt array of images when appropriate
    function SpriteArray (x,y,width,height, useWidth, useHeight,dX, dY, inArray) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.useWidth = useWidth;
        this.useHeight = useHeight;
        this.dX = dX;
        this.dY = dY;
        this.inArray = inArray;
        this.maxFrame = inArray.length-1;
        this.alpha = 1.0; //transparency of image whe drawn
        this.moveWithBackground = false;

  
        this.currentFrame = 0; //initial frame is passed

        this.collision = false;
        this.visible = true;
        // called to increment to the next image in the array
        this.advanceFrame = function(){
            if( (this.currentFrame +1) >= this.maxFrame){
                this.currentFrame = 0;
            } else {
                this.currentFrame++;
            }
        }
        this.draw = function() {
            if (this.visible) {
                ctx.globalAlpha = this.alpha; //This command sets the opacity to half - meaning you can see though any images painted after this   
                tmpImg = new Image();
                tmpImg.src = this.inArray[this.currentFrame];
                
                ctx.drawImage(tmpImg,0,0,this.width,this.height,this.x,this.y,this.useWidth,this.useHeight);
                ctx.globalAlpha = 1.0;
            }
        }
        this.checkCollisions = function(obj2) {
            if(this.x + this.useWidth > obj2.x && this.x < obj2.x + obj2.useWidth) {
                if (this.y + this.useHeight > obj2.y && this.y < obj2.y + obj2.useHeight){
                this.collision = true;
                }
            }
            bot = BottomCollision(this, obj2);
            top = TopCollision(this,obj2);
            left = LeftCollision(this,obj2);
            right = RightCollision(this,obj2);
            if ( bot || top || left || right){
                this.collision = true;
                return true;
            } else {
                this.collision = false;
                return false;
            }
        }
        //This one just checks if "this" moves one more spot down whether its bottom
        //will collide with the passed object
        this.checkBottomCollision = function(obj2) {
            return BottomCollision(this, obj2);
            
        }
        //This one just checks if "this" moves one more spot up whether its top
        //will collide with the passed object
        this.checkTopCollision = function(obj2){
            return TopCollision(this,obj2);
       }
        //This one just checks if "this" moves one more spot right whether its right
        //will collide with the passed object
        this.checkRightCollision = function(obj2) {
            return RightCollision(this,obj2);
        }
        //This one just checks if "this" moves one more spot right whether its left
        //will collide with the passed object
        this.checkLeftCollision = function(obj2) {
            return LeftCollision(this,obj2);
        }
    }
//This is a special Sprite for the background.  It will have capabilities to have it
//to be a scrolling background as certain games need this
function ScrollingBackGround(x,y,width,height, useWidth, useHeight,image){
    this.image = image;
    this.alpha = 1.0;
    this.visible = true;
    this.width = width;
    this.height = height;
    this.useWidth = useWidth;
    this.useHeight = useHeight;
    this.x = 0;
    this.y = 0;
    this.advanceBackground = true;
    // idea here is to load all terrain that will move along with the background.
    //As the background moves the terrain elements included in the background will
    //also move by changing their x & y values in lockstep
    //this.terrainArray = inArray;
    
    this.draw = function() {
        //*!*!*!*!Need to add the logic that will cause image to "wrap" around if scrolling
        if (this.visible) {
            if (this.advanceBackground){
                this.x += game.bgDX;
                this.y += game.bgDY;
            }   
            ctx.globalAlpha = this.alpha; //This command sets the opacity to half - meaning you can see though any images painted after this   

            ctx.drawImage(image,0,0,this.width,this.height,this.x,this.y,this.useWidth,this.useHeight);
            //console.log (this.x);
            var tmpX = 0;
            var tmpY = 0;
            if (this.x < 0){
                tmpX = this.useWidth+this.x;
                if (this.x == -this.useWidth){
                    this.x = 0;
                }
            } else if (this.x > 0){
                tmpX = this.x-this.useWidth;
                if (this.x == this.useWidth){
                    this.x = 0;
                }
            }
            if (this.y < 0){
                tmpY = this.useHeight+this.y;
                if (this.y == -this.useHeight){
                    this.y = 0;
                }
            } else if (this.y > 0){
                tmpY = this.y-this.useHeight;
                if (this.y == this.useHeight){
                    this.y = 0;
                }
            }
             ctx.drawImage(image, 0,0,this.width,this.height, tmpX,tmpY,this.useWidth,this.useHeight);
             
            
            ctx.globalAlpha = 1.0;
        }

        }
    }   

function createAudio(src) {
      var audio = document.createElement('audio');
      audio.src    = src;
      audio.play();
      //return audio;
    
      
    }

//** Used to help "read" the color of a specific pixel on the canvas.  Often you use 
//** this to help decide if a collision has occurred this function actually takes the 
//** three color componenents (RGB) and converts them to a hexadecimal color value. I 
//** find it easier to just compare to this one value than all 3
function rgbToHex(r, g, b) {
if (r > 255 || g > 255 || b > 255)
    throw "Invalid color component";
return ((r << 16) | (g << 8) | b).toString(16);
}
function getColor(x, y) {
    var pixelData = ctx.getImageData(x, y, 1, 1).data;
    hex = "#" + ("000000" + rgbToHex(pixelData[0], pixelData[1], pixelData[2])).slice(-6);
    return hex;
}
// This is shared by all objects that want to check for a bottom collision
function BottomCollision (obj1, obj2) {
    if(obj1.x + obj1.useWidth > obj2.x && obj1.x < obj2.x + obj2.useWidth) {
        if (obj1.y  < obj2.y + obj2.useHeight && obj1.y + obj1.useHeight + 1 > obj2.y ){
            obj1.collision = true;
            //obj1.stopJump();
            return true;
        }
    }
    return false;
}
function TopCollision (obj1, obj2) {
    if(obj1.x + obj1.useWidth > obj2.x && obj1.x < obj2.x + obj2.useWidth) {
        if (obj1.y  - 1 < obj2.y + obj2.useHeight && obj1.y  > obj2.y ){
            obj1.collision = true;
            //obj1.stopJump();
            return true;
        }
            }
            return false;
}
function RightCollision (obj1, obj2) {
    //obj1.collision = false;
    if(obj1.y + obj1.useHeight > obj2.y && obj1.y < obj2.y + obj2.useHeight) {
        if (obj1.x + obj1.useWidth + 1  > obj2.x && obj1.x < obj2.x + obj2.useWidth){
            obj1.collision = true;
            //obj1.stopJump();
            return true;
        }
    }
    return false;
}
function LeftCollision(obj1, obj2) {
    //obj1.collision = false;
    if(obj1.y + obj1.useHeight > obj2.y && obj1.y < obj2.y + obj2.useHeight) {
        if (obj1.x + obj1.useWidth   > obj2.x && obj1.x -1 < obj2.x + obj2.useWidth){
            obj1.collision = true;
            //obj1.stopJump();
            return true;
        }
    }
    return false;
}
//This Class can be used to create an object to keep track of keyboard presses and releases
//I don't currently define each key, but they are automatically defined once pressed
//I'll likley add these however so they show up in code complete
function KeysPresses(){
    this.processDownKey = function(e) {
        //console.log(e.keycode);
        switch(e.keyCode) {
            case 8:
                this.backSpace = true;
                break;
            case 9:
                this.tab = true;
                break;
            case 12:
                this.numpadCenter = true;
                break;
            case 13:
                this.enter = true;
                break;
            case 16:
                this.shift = true;
                break;
            case 17:
                this.ctrl = true;
                break;
            case 18:
                this.alt = true;
                break;
            case 19:
                this.pauseBreak = true;
                break;
            case 20:
                this.capsLock = true;
                break;
            case 27:
                this.escape = true;
                break;
            case 32:
                this.space = true;
                break;
            case 33:
                this.pageUp = true;
                break;
            case 34:
                this.pageDown = true;
                break;
            case 35:
                this.end = true;
                break;
            case 36:
                this.home = true;
                break;
            case 37:
                this.leftArrow = true;
                break;
            case 38:
                this.upArrow = true;
                break;
            case 39:
                this.rightArrow = true;
                break;
            case 40:
                this.downArrow = true;
                break;
            case 45:
                this.insert = true;
                break;
            case 46:
                this.delete = true;
                break;
            case 48:
                this.key_0 = true;
                break;
            case 49:
                this.key_1 = true;
                break;
            case 50:
                this.key_2 = true;
                break;
            case 51:
                this.key_3 = true;
                break;
            case 52:
                this.key_4 = true;
                break;
            case 53:
                this.key_5 = true;
                break;
            case 54:
                this.key_6 = true;
                break;
            case 55:
                this.key_7 = true;
                break;                
            case 56:
                this.key_8 = true;
                break;
            case 57:
                this.key_9 = true;
                break;
            case 65:
                this.key_a = true;
                break;
            case 66:
                this.key_b = true;
                break;
            case 67:
                this.key_c = true;
                break;                
            case 68:
                this.key_d = true;
                break;
            case 69:
                this.key_e = true;
                break;
            case 70:
                this.key_f = true;
                break;
            case 71:
                this.key_g = true;
                break;
            case 72:
                this.key_h = true;
                break;
            case 73:
                this.key_i = true;
                break;
            case 74:
                this.key_j = true;
                break;
            case 75:
                this.key_k = true;
                break;
            case 76:
                this.key_l = true;
                break;
            case 77:
                this.key_m = true;
                break;
            case 78:
                this.key_n = true;
                break;
            case 79:
                this.key_o = true;
                break;
            case 80:
                this.key_p = true;
                break;
            case 81:
                this.key_q = true;
                break;
            case 82:
                this.key_r = true;
                break;
            case 83:
                this.key_s = true;
                break;
            case 84:
                this.key_t = true;
                break;
            case 85:
                this.key_u = true;
                break;
            case 86:
                this.key_v = true;
                break;
            case 87:
                this.key_w = true;
                break;
            case 88:
                this.key_x = true;
                break;
            case 89:
                this.key_y = true;
                break;
            case 90:
                this.key_z = true;
                break;
            case 91:
                this.leftWindowKey = true;
                break;
            case 92:
                this.rightWindowKey = true;
                break;
            case 93:
                this.selectKey = true;
                break;
            case 96:
                this.numpad0 = true;
                break;
            case 97:
                this.numpad1 = true;
                break;
            case 98:
                this.numpad2 = true;
                break;
            case 99:
                this.numpad3 = true;
                break;
            case 100:
                this.numpad4 = true;
                break;
            case 101:
                this.numpad5 = true;
                break;
            case 102:
                this.numpad6 = true;
                break;
            case 103:
                this.numpad7 = true;
                break;
            case 104:
                this.numpad8 = true;
                break;
            case 105:
                this.numpad9 = true;
                break;
            case 106:
                this.multiplyKey = true;
                break;
            case 107:
                this.addKey = true;
                break;
            case 109:
                this.subtractKey = true;
                break;
            case 110:
                this.decimalPoint = true;
                break;
            case 111:
                this.divideKey = true;
                break;
            case 112:
                e.preventDefault();
                this.f1 = true;
                break;
            case 113:
                this.f2 = true;
                break;
            case 114:
                this.f3 = true;
                break;
            case 115:
                this.f4 = true;
                break;
            case 116:
                this.f5 = true;
                break;
            case 117:
                this.f6 = true;
                break;
            case 118:
                this.f7 = true;
                break;
            case 119:
                this.f8 = true;
                break;
            case 120:
                this.f9 = true;
                break;
            case 121:
                this.f10 = true;
                break;
            case 122:
                this.f11 = true;
                break;
            case 123:
                this.f12 = true;
                break;
            case 144:
                this.numLock = true;
                break;
            case 145:
                this.scrollLock = true;
                break;
            case 186:
                this.semiColon = true;
                break;
            case 187:
                this.equalSign = true;
                break;
            case 188:
                this.comma = true;
                break;
            case 189:
                this.dash = true;
                break;
            case 190:
                this.period = true;
                break;
            case 191:
                this.forwardSlash = true;
                break;
            case 192:
                this.graveAccent = true;
                break;
            case 219:
                this.graveAccent = true;
                break;
            case 220:
                this.backSlash = true;
                break;
            case 221:
                this.closeBracket = true;
                break;
            case 222:
                this.singleQuote = true;
                break;
            default:
                //No action
        }

    }
    this.processUpKey = function(e) {
        switch(e.keyCode) {
            case 8:
                this.backSpace = false;
                break;
            case 9:
                this.tab = false;
                break;
            case 12:
                this.numpadCenter = false;
                break;
            case 13:
                this.enter = false;
                break;
            case 16:
                this.shift = false;
                break;
            case 17:
                this.ctrl = false;
                break;
            case 18:
                this.alt = false;
                break;
            case 19:
                this.pauseBreak = false;
                break;
            case 20:
                this.capsLock = false;
                break;
            case 27:
                this.escape = false;
                break;
            case 32:
                this.space = false;
                break;
            case 33:
                this.pageUp = false;
                break;
            case 34:
                this.pageDown = false;
                break;
            case 35:
                this.end = false;
                break;
            case 36:
                this.home = false;
                break;
            case 37:
                this.leftArrow = false;
                break;
            case 38:
                this.upArrow = false;
                break;
            case 39:
                this.rightArrow = false;
                break;
            case 40:
                this.downArrow = false;
                break;
            case 45:
                this.insert = false;
                break;
            case 46:
                this.delete = false;
                break;
            case 48:
                this.key_0 = false;
                break;
            case 49:
                this.key_1 = false;
                break;
            case 50:
                this.key_2 = false;
                break;
            case 51:
                this.key_3 = false;
                break;
            case 52:
                this.key_4 = false;
                break;
            case 53:
                this.key_5 = false;
                break;
            case 54:
                this.key_6 = false;
                break;
            case 55:
                this.key_7 = false;
                break;                
            case 56:
                this.key_8 = false;
                break;
            case 57:
                this.key_9 = false;
                break;
            case 65:
                this.key_a = false;
                break;
            case 66:
                this.key_b = false;
                break;
            case 67:
                this.key_c = false;
                break;                
            case 68:
                this.key_d = false;
                break;
            case 69:
                this.key_e = false;
                break;
            case 70:
                this.key_f = false;
                break;
            case 71:
                this.key_g = false;
                break;
            case 72:
                this.key_h = false;
                break;
            case 73:
                this.key_i = false;
                break;
            case 74:
                this.key_j = false;
                break;
            case 75:
                this.key_k = false;
                break;
            case 76:
                this.key_l = false;
                break;
            case 77:
                this.key_m = false;
                break;
            case 78:
                this.key_n = false;
                break;
            case 79:
                this.key_o = false;
                break;
            case 80:
                this.key_p = false;
                break;
            case 81:
                this.key_q = false;
                break;
            case 82:
                this.key_r = false;
                break;
            case 83:
                this.key_s = false;
                break;
            case 84:
                this.key_t = false;
                break;
            case 85:
                this.key_u = false;
                break;
            case 86:
                this.key_v = false;
                break;
            case 87:
                this.key_w = false;
                break;
            case 88:
                this.key_x = false;
                break;
            case 89:
                this.key_y = false;
                break;
            case 90:
                this.key_z = false;
                break;
            case 91:
                this.leftWindowKey = false;
                break;
            case 92:
                this.rightWindowKey = false;
                break;
            case 93:
                this.selectKey = false;
                break;
            case 96:
                this.numpad0 = false;
                break;
            case 97:
                this.numpad1 = false;
                break;
            case 98:
                this.numpad2 = false;
                break;
            case 99:
                this.numpad3 = false;
                break;
            case 100:
                this.numpad4 = false;
                break;
            case 101:
                this.numpad5 = false;
                break;
            case 102:
                this.numpad6 = false;
                break;
            case 103:
                this.numpad7 = false;
                break;
            case 104:
                this.numpad8 = false;
                break;
            case 105:
                this.numpad9 = false;
                break;
            case 106:
                this.multiplyKey = false;
                break;
            case 107:
                this.addKey = false;
                break;
            case 109:
                this.subtractKey = false;
                break;
            case 110:
                this.decimalPoint = false;
                break;
            case 111:
                this.divideKey = false;
                break;
            case 112:
                this.f1 = false;
                break;
            case 113:
                this.f2 = false;
                break;
            case 114:
                this.f3 = false;
                break;
            case 115:
                this.f4 = false;
                break;
            case 116:
                this.f5 = false;
                break;
            case 117:
                this.f6 = false;
                break;
            case 118:
                this.f7 = true;
                break;
            case 119:
                this.f8 = false;
                break;
            case 120:
                this.f9 = false;
                break;
            case 121:
                this.f10 = false;
                break;
            case 122:
                this.f11 = false;
                break;
            case 123:
                this.f12 = false;
                break;
            case 144:
                this.numLock = false;
                break;
            case 145:
                this.scrollLock = false;
                break;
            case 186:
                this.semiColon = false;
                break;
            case 187:
                this.equalSign = false;
                break;
            case 188:
                this.comma = false;
                break;
            case 189:
                this.dash = false;
                break;
            case 190:
                this.period = false;
                break;
            case 191:
                this.forwardSlash = false;
                break;
            case 192:
                this.graveAccent = false;
                break;
            case 219:
                this.graveAccent = false;
                break;
            case 220:
                this.backSlash = false;
                break;
            case 221:
                this.closeBracket = false;
                break;
            case 222:
                this.singleQuote = false;
                break;
            default:
                //No action
        }

    }
    this.processMouseMove = function(e) {
        this.mouseX = e.clientX;
        this.mouseY = e.clientY;
        console.log("X:" + this.mouseX + " Y: " + this.mouseY);
    }
    this.processMouseClick = function(e) {
        //console.log("Mousebutton: " + e.which + " Click");
        switch(e.which) {
            case 1:
                this.mouseLeftButtonClick = true;
                break;
            case 2:
                this.mouseMiddleButtonClick = true;
                break;
            case 2:
                this.mouseRightButtonClick = true;
                break;
        }
    }
    this.processMouseUp = function(e) {
        //console.log("Mouse Button " + e.which + " Up X:" + this.mouseX + " Y: " + this.mouseY);
        switch(e.which) {
            case 1:
                this.mouseLeftButtonUp = true;
                break;
            case 2:
                this.mouseMiddleButtonUp = true;
                break;
            case 2:
                this.mouseRightButtonUp = true;
                break;
        }
    }
    this.processMouseDown = function(e) {
        //console.log("Mouse Button " + e.which + " Down X:" + this.mouseX + " Y: " + this.mouseY);
        switch(e.which) {
            case 1:
                this.mouseLeftButtonDown = true;
                break;
            case 2:
                this.mouseMiddleButtonDown = true;
                break;
            case 2:
                this.mouseRightButtonDown = true;
                break;
        }
    }
}