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