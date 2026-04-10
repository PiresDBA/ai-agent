$(document).ready(function () {
    const ariplanesNumber = 100
    const canvasSize = 700;
    const mousePosThreshold = Math.floor(canvasSize / 100);

    var canvas = document.getElementById("airplanesCanvas");
    var ctx = canvas.getContext('2d');
    canvas.width = canvasSize;
    canvas.height = canvasSize;


    var bgSprite = new Image();
    bgSprite.src = "sprite/bg.jpg";
    bgSprite.onload = function () { };

    var airplaneSprite = new Image();
    airplaneSprite.src = "sprite/airplane.png";
    airplaneSprite.onload = function () {
        spawn();
    };

    var mouseX;
    var mouseY;
    var rectBounds = canvas.getBoundingClientRect();
    var testBool = false;


    function Airplane() {
        this.speed = 100;
        this.x = 1;
        this.y = 1;
        this.width = 25;
        this.height = 25;

        this.randomizePos = function () {
            this.x = Math.floor((Math.random() * canvas.width) - (this.width / 2));
            this.y = Math.floor((Math.random() * canvas.height) - (this.height / 2));
        };

        this.respawn = function () {
            this.randomizePos();
            ctx.drawImage(airplaneSprite, this.x, this.y, this.width, this.height);
        };

        this.render = function () {
            ctx.drawImage(airplaneSprite, this.x, this.y, this.width, this.height);
        };

        this.update = function (modifier) {
            if (
                (this.x > (mouseX - mousePosThreshold) && this.x < (mouseX + mousePosThreshold)) &&
                (this.y < (mouseY + mousePosThreshold) && this.y > (mouseY - mousePosThreshold))
            ) {
                console.log("Respawning Ariplane", this.x, this.y);
                this.respawn();
            }

            console.log("Mouse Pos", mouseX, mouseY);
            console.log("Ariplane Pos", this.x, this.y);

            if (this.x < mouseX && this.y < mouseY) {
                this.x += (this.speed * modifier);
                this.y += (this.speed * modifier);
            }

            if (this.x > (mouseX) && this.y > mouseY) {
                this.x -= (this.speed * modifier);
                this.y -= (this.speed * modifier);
            }

            if (this.y < mouseY && this.x > mouseX) {
                this.x -= (this.speed * modifier);
                this.y += (this.speed * modifier);
            }

            if (this.y > mouseY && this.x < mouseX) {
                this.y -= (this.speed * modifier);
                this.x += (this.speed * modifier);
            }
        }
    }

    function renderBackground() {
        ctx.drawImage(bgSprite, 0, 0, canvas.width, canvas.height);
    }

    var squareX;

    function renderSquare() {
        ctx.rect((mouseX - 10), (mouseY - 10), 20, 20);
        ctx.lineWidth = 1;
        ctx.strokeStyle = "black";
        ctx.stroke();
        squareX = (mouseX - 10);
    }

    $("#airplanesCanvas").mousemove(function (e) {
        mouseX = (e.clientX - rectBounds.left);
        mouseY = (e.clientY - rectBounds.top);
    });

    var airplaneArray = [];

    function spawn() {
        renderBackground();
        for (var i = 0; i < ariplanesNumber; i++) {
            var airplane = new Airplane();
            airplane.randomizePos();
            airplane.render();
            airplaneArray.push(airplane);
            console.log(airplane.x, airplane.y);
        }
        console.log(airplaneArray);
        console.log(testBool);
    }

    var thisAirplane;

    /*****Loop Principale del gioco*****/
    var main = function () {
        var now = Date.now();
        var delta = now - then;

        renderSquare();
        renderBackground();

        for (var i = 0; i < ariplanesNumber; i++) {
            thisAirplane = airplaneArray[i];
            thisAirplane.update(delta / 1000);
            thisAirplane.render();
        }

        then = now;
        requestAnimationFrame(main);
    };


    var then;

    $(document).on('keydown', function () {
        then = Date.now();
        main();
    });

});