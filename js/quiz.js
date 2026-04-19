var answers={name:'',age:'',size:'',concern:'',symptom:''};
var current=0;

function setLang(l){
  document.querySelectorAll('.es').forEach(e=>e.style.display=l==='es'?'':'none');
  document.querySelectorAll('.en').forEach(e=>e.style.display=l==='en'?'':'none');
  document.querySelectorAll('.lang-btn').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.lang-btn').forEach(b=>{if(b.textContent===l.toUpperCase())b.classList.add('active')});
}

function updateProgress(){
  for(var i=1;i<=5;i++){
    var d=document.getElementById('d'+i);
    d.classList.remove('active','done');
    if(i<current)d.classList.add('done');
    else if(i===current)d.classList.add('active');
  }
}

function goTo(n){
  document.querySelectorAll('.step').forEach(s=>s.classList.remove('active'));
  if(n===0)document.getElementById('step0').classList.add('active');
  else if(n>=1&&n<=5)document.getElementById('step'+n).classList.add('active');
  else document.getElementById('stepResult').classList.add('active');
  current=n;
  updateProgress();
  window.scrollTo({top:0,behavior:'smooth'});
  if(n===1)setTimeout(()=>document.getElementById('dog-name-input').focus(),400);
}

function onNameInput(){
  var v=document.getElementById('dog-name-input').value.trim();
  document.getElementById('name-next').disabled=v.length===0;
}

function submitName(){
  var v=document.getElementById('dog-name-input').value.trim();
  if(!v)return;
  answers.name=v;
  updateDogNameDisplay();
  goTo(2);
}

function updateDogNameDisplay(){
  var n=answers.name||'tu perro';
  document.querySelectorAll('.dog-name').forEach(el=>{el.textContent=n});
  document.querySelectorAll('.dog-name-up').forEach(el=>{el.textContent=n.toUpperCase()});
}

function pickOption(el,key,val){
  el.parentElement.querySelectorAll('.option').forEach(o=>o.classList.remove('picked'));
  el.classList.add('picked');
  answers[key]=val;
  setTimeout(function(){
    if(key==='age')goTo(3);
    else if(key==='size')goTo(4);
    else if(key==='concern')goTo(5);
    else if(key==='symptom')showResult();
  },400);
}

var PRODUCTS={
  condroprotector:{
    title:'Condroprotector',
    img:'images/doypack-condroprotector.webp',
    alt_es:'Doypack Bondi Pets Condroprotector para articulaciones',
    alt_en:'Bondi Pets Joint Support doypack',
    bullets_es:['Glucosamina + Condroitín + MSM','Piperina para máxima absorción (+2000%)','Probiótico Bacillus subtilis'],
    bullets_en:['Glucosamine + Chondroitin + MSM','Piperine for maximum absorption (+2000%)','Bacillus subtilis probiotic']
  },
  biotics:{
    title:'Pre+Pro+Post Biotics',
    img:'images/doypack-biotics.webp',
    alt_es:'Doypack Bondi Pets Pre+Pro+Post Biotics para digestión',
    alt_en:'Bondi Pets Pre+Pro+Post Biotics doypack',
    bullets_es:['Pre + Pro + Postbióticos triple acción','Microbioma equilibrado','Enzimas digestivas'],
    bullets_en:['Pre + Pro + Postbiotics triple action','Balanced microbiome','Digestive enzymes']
  },
  multivitamin:{
    title:'Multivitamin',
    img:'images/doypack-multivitamin.webp',
    alt_es:'Doypack Bondi Pets Multivitamin con vitaminas y minerales',
    alt_en:'Bondi Pets Multivitamin doypack',
    bullets_es:['Vitaminas A, B, C, D, E completas','Minerales esenciales (zinc, hierro)','Antioxidantes naturales'],
    bullets_en:['Complete A, B, C, D, E vitamins','Essential minerals (zinc, iron)','Natural antioxidants']
  }
};

function decide(){
  var s=answers.symptom,c=answers.concern;
  var p;
  if(s==='stiffness')p='condroprotector';
  else if(s==='soft_stools')p='biotics';
  else if(s==='less_energy')p='multivitamin';
  else {
    if(c==='mobility')p='condroprotector';
    else if(c==='digestion')p='biotics';
    else if(c==='energy')p='multivitamin';
    else p='condroprotector';
  }
  var seniorJoint=(answers.age==='senior'&&(c==='mobility'||s==='stiffness'));
  return {product:p,seniorJoint:seniorJoint};
}

function currentLang(){
  var active=document.querySelector('.lang-btn.active');
  return active?active.textContent.toLowerCase():'es';
}

function showResult(){
  var r=decide();
  var p=PRODUCTS[r.product];
  var lang=currentLang();
  document.getElementById('result-title').textContent=p.title;
  var img=document.getElementById('result-img');
  img.src=p.img;
  img.alt=lang==='es'?p.alt_es:p.alt_en;
  var ul=document.getElementById('result-bullets');
  ul.innerHTML='';
  var bullets_es=p.bullets_es,bullets_en=p.bullets_en;
  for(var i=0;i<bullets_es.length;i++){
    var li=document.createElement('li');
    var spEs=document.createElement('span');spEs.className='es';spEs.textContent=bullets_es[i];
    var spEn=document.createElement('span');spEn.className='en';spEn.style.display=lang==='en'?'':'none';spEn.textContent=bullets_en[i];
    if(lang==='en')spEs.style.display='none';
    li.appendChild(spEs);li.appendChild(spEn);
    ul.appendChild(li);
  }
  document.getElementById('result-senior').style.display=r.seniorJoint?'block':'none';
  updateDogNameDisplay();
  goTo(6);
}

function resetQuiz(){
  answers={name:'',age:'',size:'',concern:'',symptom:''};
  document.getElementById('dog-name-input').value='';
  document.getElementById('name-next').disabled=true;
  document.querySelectorAll('.option').forEach(o=>o.classList.remove('picked'));
  document.getElementById('quiz-email').value='';
  document.getElementById('quiz-email').disabled=false;
  document.getElementById('quiz-success').style.display='none';
  document.getElementById('quiz-error').style.display='none';
  goTo(0);
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
    i.disabled=true;s.style.display='block';
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
