$(document).ready(function(){

 // Show Input element
 $('.edit').click(function(){
  $('.txtedit').hide();
  $(this).next('.txtedit').show().focus();
  $(this).hide();
 });

 // Save data
 $(".txtedit").focusout(function(){

  // Get edit id, field name and value
  var id = this.id;
  var data_name = this.dataset.name;
  var data_pk = this.dataset.pk;
  var value = $(this).val();

  // Hide Input element
  $(this).hide();

  // Hide and Change Text of the container with input elmeent
  $(this).prev('.edit').show();
  $(this).prev('.edit').text(value);

  update_product(data_name, value, data_pk);

 });
  $(".txtedit").focusout(function(){

  // Get edit id, field name and value
  var data_name = this.dataset.name;
  var data_pk = this.dataset.pk;
  var value = $(this).val();

  // Hide Input element
  $(this).hide();

  // Hide and Change Text of the container with input elmeent
  $(this).prev('.edit').show();
  $(this).prev('.edit').text(value);

  update_product('/update_product', data_name, value, data_pk);

 });

  $(".txtedit_shop").focusout(function(){

  // Get edit id, field name and value
  var data_name = this.dataset.name;
  var data_pk = this.dataset.pk;
  var value = $(this).val();

  update_product('/update_shop', data_name, value, data_pk);

 });
 $(".txtedit_receipt").focusout(function(){

  // Get edit id, field name and value
  var data_name = this.dataset.name;
  var data_pk = this.dataset.pk;
  var value = $(this).val();

  update_product('/update_receipt', data_name, value, data_pk);

 });

});




function update_product(url, data_name, value, data_pk) {
  $.ajax({
   url: url,
   type: 'POST',
   data: { name:data_name, value:value, pk:data_pk },
   success:function(response){
      if(response == 1){
         console.log('Save successfully');
      }else{
         console.log("Not saved.");
      }
   }
  });
}

$(document).ready(function(){
    var dataTable = $('#data_table').DataTable();
});

$(document).ready(function(){
    var dataTable = $('#data_table_receipt').DataTable({
        order: [[0, 'desc']],
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

function show_line(pos_top, pos_left, pos_width, pos_height, del_button_id) {
    var canvas = document.getElementById("myCanvas");
    var ctx = canvas.getContext("2d");
    if (del_button_id != null) {
        var del_button = document.getElementById(del_button_id);
        del_button.style.display = 'block';
    }
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
    var del_buttons = document.getElementsByClassName('delbutton');
    for (var i = 0, row; row = del_buttons[i]; i++) {
        del_buttons[i].style.display = 'none';
    }
    var ctx = canvas.getContext("2d");
    let box = document.getElementById('receiptimg');
    let width = $( "#img_receipt" ).width();
    let height = $( "#img_receipt" ).height();
    ctx.clearRect(0,0,width,height);
}

