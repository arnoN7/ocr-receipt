$(document).ready(function(){
    var dataTable = $('#data_table').DataTable();
    $('#data_table').editable({
        container:'body',
        selector:'td.name',
        url:'/update_product',
        title:'name',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        }
    });

    $('#data_table').editable({
        container:'body',
        selector:'td.email',
        url:'/update_product',
        title:'Email',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        }
    });

    $('#data_table').editable({
        container:'body',
        selector:'td.phone',
        url:'/update_product',
        title:'Phone',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        }
    });

    $('#data_table').editable({
        container:'body',
        selector:'td.quantity',
        url:'/update_product',
        title:'quantity',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        }
    });

    $('#data_table').editable({
        container:'body',
        selector:'td.price',
        url:'/update_product',
        title:'price',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        }
    });

    $('#data_table').editable({
        container:'body',
        selector:'td.unit_price',
        url:'/update_product',
        title:'unit_price',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        }
    });
});

function draw() {
  console.log("tt");
  let ctx = document.getElementById('canvas').getContext('2d');
  let img = new Image();
  img.onload = function() {
    ctx.drawImage(img, 0, 0);
    ctx.beginPath();
    ctx.moveTo(30, 96);
    ctx.lineTo(70, 66);
    ctx.lineTo(103, 76);
    ctx.lineTo(170, 15);
    ctx.stroke();
  };
  img.src = 'backdrop.png';
}

function drawBorder(ctx, xPos, yPos, width, height, thickness = 1)
{
  ctx.fillStyle='#FFFFFF';
  ctx.fillRect(xPos - (thickness), yPos - (thickness), width + (thickness * 2), height + (thickness * 2));
}

function show_line(pos_top, pos_left, pos_width, pos_height) {
    var canvas = document.getElementById("myCanvas");
    var ctx = canvas.getContext("2d");
    ctx.restore();
    let box = document.getElementById('receiptimg');
    let width = $( "#img_receipt" ).width();
    let height = $( "#img_receipt" ).height();
    ctx.globalAlpha = 0.4;
    ctx.fillStyle = "#FFFF00";
    ctx.strokeStyle = 'red';
    ctx.stroke();
    ctx.fillRect(0,0,pos_width*width,pos_height*height);
    canvas.style.top = (pos_top*height)+"px";
    canvas.style.left = (pos_left*width)+"px";
    ctx.save();
}
function hide_show_line() {
    var canvas = document.getElementById("myCanvas");
    var ctx = canvas.getContext("2d");
    let box = document.getElementById('receiptimg');
    let width = $( "#img_receipt" ).width();
    let height = $( "#img_receipt" ).height();
    ctx.clearRect(0,0,width,height);
}

