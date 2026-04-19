function setLang(l){
  document.querySelectorAll('.es').forEach(e=>e.style.display=l==='es'?'':'none');
  document.querySelectorAll('.en').forEach(e=>e.style.display=l==='en'?'':'none');
  document.querySelectorAll('.lang-btn').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.lang-btn').forEach(b=>{if(b.textContent===l.toUpperCase())b.classList.add('active')});
}
var baseCount=143;
function animateCounter(){
  baseCount++;
  ['counter-num','counter-num2','counter-num3'].forEach(id=>{var el=document.getElementById(id);if(el)el.textContent=baseCount;});
}
function submitEmail(inputId,successId,btnSelector,errorId){
  var i=document.getElementById(inputId);
  var s=document.getElementById(successId);
  var e=errorId?document.getElementById(errorId):null;
  var b=document.querySelector(btnSelector);
  if(e)e.style.display='none';
  if(!(i.value&&i.value.includes('@'))){
    i.style.outline='3px solid #FF2D87';setTimeout(function(){i.style.outline=''},1000);
    return;
  }
  if(b)b.disabled=true;
  var form=document.getElementById('ml-form');
  var iframe=document.getElementById('ml-target');
  document.getElementById('ml-email').value=i.value;
  var settled=false;
  var onLoad=function(){
    if(settled)return;settled=true;
    iframe.removeEventListener('load',onLoad);
    i.disabled=true;s.style.display='block';animateCounter();
  };
  iframe.addEventListener('load',onLoad);
  setTimeout(function(){
    if(settled)return;settled=true;
    iframe.removeEventListener('load',onLoad);
    if(b)b.disabled=false;
    if(e)e.style.display='block';
  },8000);
  form.submit();
}
function toggleFaq(el){
  var item=el.parentElement;
  var wasOpen=item.classList.contains('open');
  document.querySelectorAll('.faq-item').forEach(f=>f.classList.remove('open'));
  if(!wasOpen)item.classList.add('open');
}
