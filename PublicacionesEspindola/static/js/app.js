const menuData = [
  ['🗂','1.Catalogos',[
    ['1.Proveedores','catalog','suppliers'],
    ['2.Clientes',null,null,[['1.Prioridades','report'],['2.Grupos de Clientes','report'],['3.Altas','form','customers'],['4.Consultas','catalog','customers'],['5.Modificaciones','catalog','customers'],['7.Modificaciones de Sucursal','report'],['8.Reportes','report'],['9.Rutas','report']]],
    ['3.Revistas','catalog','publications'],['4.Empleados','report'],['5.Cuentas','report']]],
  ['📄','2.Compras',[
    ['1.Facturas','operation','COMPRA'],
    ['2.Cuentas por Pagar',null,null,[['1.Altas','operation','CUENTA POR PAGAR'],['2.Consultas','operations'],['3.Reporte de Liquidacion','report'],['4.Estado de Cuenta','report']]],
    ['3.Devoluciones',null,null,[['1.Altas','operation','DEVOLUCION A PROVEEDOR'],['2.Reportes de Predevolucion','report'],['3.Consultas','operations']]],
    ['4.Reporte Estadistico de Compras','report']]],
  ['📰','3.Ventas',[
    ['1.Paquetes',null,null,[['1.Altas','operation','PAQUETE'],['2.Consultas','operations'],['3.Paquete Maestro','report'],['4.Reporte Distribucion de Locales Cerrados','report']]],
    ['2.Pedidos',null,null,[['1.Consultas','operations']]],
    ['3.Facturas',null,null,[['1.Altas','operation','VENTA'],['2.Consultas','operations'],['3.Para Contabilidad','report'],['4.Relacion Tiket','report'],['5.Alta x Grupos','report'],['6.Reporte de Rutas','report'],['7.Reporte de Venta x Revistas','report'],['8.Reporte Mensual SAT','report']]],
    ['4.Devoluciones',null,null,[['1.Normal','operation','DEVOLUCION DE CLIENTE'],['2.Cancelacion','operation','CANCELACION'],['3.Extemporanea','operation','DEVOLUCION EXTEMPORANEA'],['4.Consultas','operations'],['5.Para Contabilidad','report'],['6.Relacion Tikets','report'],['7.Reporte de Pre-Devolucion','report'],['8.Rep. de Devoluciones x Revista','report']]],
    ['5.Cuentas por Cobrar',null,null,[['1.Altas','operation','CUENTA POR COBRAR'],['2.Consultas','operations'],['3.Estado de Cuenta','report'],['4.Estado de Cuenta x Grupo','report']]],
    ['6.Corte de Caja',null,null,[['1.Del Dia General','report'],['2.Flujo de Efectivo','report'],['3.Corte detallado','report'],['4.Consulta de Vales','report'],['5.Movimientos de Clientes','report']]],
    ['7.Reporte de Distribucion','report'],['8.Conciliacion','report'],['9.Reporte Estadistico de Ventas','report']]],
  ['A','4.Inventario',[
    ['1.Ediciones',null,null,[['1.Consultas','catalog','editions'],['2.Modificaciones','catalog','editions'],['3.Reporte de Existencias x Revista','report'],['4.Reporte de Inventario','report']]],
    ['2.Traspasos',null,null,[['1.Alta de Traspasos','operation','TRASPASO'],['2.Consulta','operations']]],
    ['3.Tipo de Movimientos',null,null,[['1.Altas','report'],['2.Consultas','report'],['3.Modificaciones','report']]]]],
  ['🚫','5.Cancelaciones', [['1.Compras','operation','CANCELACION DE COMPRA'],['3.Devolucion x Bodega','operation','DEVOLUCION POR BODEGA'],['4.Devolucion x Devolucion','operation','CANCELACION DE DEVOLUCION']]],
  ['❔','8.Ayuda', [['Acerca de SADYV','about']]],
  ['🔧','9.Salir', [['Salir del sistema','exit']]]
];

const toolbar = [
  ['💰','Ventas',()=>openOperation('VENTA')],['▤','Consultas',()=>openCatalog('operations','Consulta de Ventas')],
  ['👥','Clientes',()=>openCatalog('customers','MODULO DE CLIENTES')],['▰','Edo.Cta.',()=>openReport('Estado de Cuenta')],
  ['▦','Flujo Efec.',()=>openReport('Flujo de Efectivo')],['◀','Devolucion',()=>openOperation('DEVOLUCION DE CLIENTE')],
  ['▣','Consultas',()=>openCatalog('editions','Consulta de Ediciones')]
];

const columns = {
  customers: [['code','Clave'],['name','Nombre'],['rfc','R.F.C.'],['phone','Teléfono'],['city','Ciudad'],['balance','Saldo']],
  suppliers: [['code','Clave'],['name','Nombre'],['rfc','Reg. Fed. Caus.'],['phone','Teléfono'],['balance','Saldo']],
  publications: [['code','Clave revista'],['title','Título'],['barcode','Código de barras'],['tax','I.V.A.']],
  editions: [['publication_code','Clave revista'],['title','Nombre Revista'],['number','No. Edición'],['name','Edición'],['price','Precio'],['stock','Existencia'],['arrival_date','Fecha Entrada']],
  operations: [['kind','Movimiento'],['folio','Folio'],['operation_date','Fecha'],['party_code','Clave'],['party_name','Nombre'],['total','Total']]
};

function buildMenus(){
  const nav=document.querySelector('#main-menu');
  menuData.forEach(([icon,label,items])=>{
    const root=document.createElement('div'); root.className='menu-root';
    root.innerHTML=`<button class="menu-label"><span class="ico">${icon}</span>${label}</button>`;
    root.appendChild(dropdown(items)); nav.appendChild(root);
    root.firstChild.onclick=e=>{e.stopPropagation();document.querySelectorAll('.menu-root').forEach(x=>x!==root&&x.classList.remove('open'));root.classList.toggle('open')};
  });
  document.onclick=()=>document.querySelectorAll('.menu-root').forEach(x=>x.classList.remove('open'));
}
function dropdown(items){
  const d=document.createElement('div');d.className='dropdown';
  items.forEach(([label,action,arg,children])=>{
    const holder=document.createElement(children?'div':'button');holder.className=children?'submenu-item':'menu-item';
    if(children){holder.innerHTML=`<button class="menu-item has-next">${label}</button>`;holder.appendChild(dropdown(children));}
    else{holder.textContent=label;holder.onclick=e=>{e.stopPropagation();run(action,arg,label);closeMenus()};}
    d.appendChild(holder);
  });return d;
}
function closeMenus(){document.querySelectorAll('.menu-root').forEach(x=>x.classList.remove('open'))}
function run(action,arg,label){
  if(action==='catalog')openCatalog(arg,label); else if(action==='form')openForm(arg);
  else if(action==='operation')openOperation(arg); else if(action==='operations')openCatalog('operations',label);
  else if(action==='report')openReport(label); else if(action==='about')openAbout();
  else if(action==='exit')window.close();
}
function buildToolbar(){const t=document.querySelector('#toolbar');toolbar.forEach(([i,l,fn])=>{const b=document.createElement('button');b.className='tool';b.innerHTML=`<span class="tool-icon">${i}</span>${l}`;b.onclick=fn;t.appendChild(b)})}
function win(title,compact=false){
  document.querySelectorAll('.mdi-window').forEach(x=>x.remove());
  const w=document.createElement('section');w.className='mdi-window'+(compact?' compact':'');
  w.innerHTML=`<div class="mdi-title"><span>▧</span>&nbsp;<b>${title}</b><div class="mdi-controls"><button>_</button><button>□</button><button class="close">×</button></div></div>`;
  w.querySelector('.close').onclick=()=>w.remove();document.querySelector('#windows').appendChild(w);return w;
}
async function openCatalog(entity,title){
  const w=win(title || entity.toUpperCase());
  w.insertAdjacentHTML('beforeend',`<div class="module-nav"><button>Altas</button><button>Consultas</button><button>Modificaciones</button><button class="nav-exit">Salir</button></div><div class="module-heading"><strong>CARLOS ESPINDOLA</strong><strong>CARLOS ESPINDOLA</strong><span>Catálogo de ${title||entity}</span></div><div class="searchbar"><label>Buscar&nbsp; <input class="query" autofocus></label><button class="win-button find">🔎 Buscar</button><button class="win-button add">➕ Alta</button></div><div class="table-wrap"><table class="data-table"><thead><tr>${columns[entity].map(x=>`<th>${x[1]}</th>`).join('')}</tr></thead><tbody></tbody></table></div><div class="status-mini">${today()} &nbsp;&nbsp; Consulta del catálogo</div>`);
  w.querySelector('.nav-exit').onclick=()=>w.remove(); w.querySelector('.add').onclick=()=>entity==='operations'?openOperation('MOVIMIENTO'):openForm(entity);
  const load=async()=>{const rows=await fetch(`/api/${entity}?q=${encodeURIComponent(w.querySelector('.query').value)}`).then(r=>r.json());w.querySelector('tbody').innerHTML=rows.map(row=>`<tr>${columns[entity].map(([key])=>`<td>${format(row[key],key)}</td>`).join('')}</tr>`).join('')};
  w.querySelector('.find').onclick=load;w.querySelector('.query').onkeydown=e=>e.key==='Enter'&&load();load();
}
function formFields(entity){
  if(entity==='customers')return [['code','Clave'],['rfc','R. F. C.'],['name','Nombre','wide'],['address','Dirección','wide'],['city','Ciudad'],['phone','Teléfono(s)'],['email','Email'],['discount','Descuento (%)'],['credit_limit','Límite Crédito'],['balance','Saldo Inicial']];
  if(entity==='suppliers')return [['code','Clave'],['rfc','Reg. Fed. Caus.'],['name','Nombre'],['address','Dirección'],['phone','Teléfono'],['email','Email'],['balance','Saldo']];
  return [['code','Clave revista'],['supplier_id','Clave Proveedor'],['title','Nombre Revista','wide'],['barcode','Código de Barras'],['tax','I.V.A. (%)']];
}
function openForm(entity){
  const names={customers:'MODULO DE CLIENTES',suppliers:'Modulo de Proveedores',publications:'Modulo de Revistas'};const w=win(names[entity]||'Catálogo',true);const fields=formFields(entity);
  w.insertAdjacentHTML('beforeend',`<div class="module-nav"><button>Altas</button><button>Consultas</button><button>Modificaciones</button><button class="nav-exit">Salir</button></div><div class="module-heading"><strong>CARLOS ESPINDOLA</strong><strong>CARLOS ESPINDOLA</strong><span>Alta de ${entity==='customers'?'cliente':entity==='suppliers'?'proveedor':'revista'}</span></div><div class="tabs"><button class="tab">Datos Generales</button><button class="tab">Condiciones</button></div><form class="form-area"><div class="form-grid">${fields.map(([key,label,wide])=>`<label>${label}</label><input name="${key}" class="${wide==='wide'?'span3':''}">`).join('')}</div></form><div class="button-row"><button class="win-button save">💾 Guardar</button><button class="win-button nav-exit">🚪 Salir</button></div><div class="status-mini">${today()} &nbsp;&nbsp; CLAVE DEL REGISTRO</div>`);
  w.querySelectorAll('.nav-exit').forEach(b=>b.onclick=()=>w.remove());
  w.querySelector('.save').onclick=async()=>{const data=Object.fromEntries(new FormData(w.querySelector('form')));const r=await fetch(`/api/${entity}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const out=await r.json();if(r.ok){toast('Registro guardado correctamente');w.remove();openCatalog(entity,names[entity])}else toast(out.error||'No fue posible guardar')};
}
function openOperation(kind){
  const title=kind.includes('COMPRA')?'Modulo de Compras':kind.includes('PROVEEDOR')?'Devolucion a Proveedores(Almacen Devoluciones)':kind==='VENTA'?'Modulo de Ventas':kind;const w=win(title);
  const folio=String(Date.now()).slice(-6);const isSale=kind==='VENTA';const isTransfer=kind==='TRASPASO';const isSupplier=kind.includes('COMPRA')||kind.includes('PROVEEDOR')||kind.includes('BODEGA');
  w.insertAdjacentHTML('beforeend',`<div class="operation-head"><label>Folio Interno</label><input name="folio" value="${folio}" readonly><label>Fecha</label><input name="operation_date" value="${today()}"><label>Clave ${isSupplier?'Proveedor':'Cliente'}</label><input name="party_code"><label>Nombre</label><input name="party_name">${isSale?'<label>Tipo de Venta</label><select name="sale_type"><option>CONTADO</option><option>CREDITO</option></select>':''}${isTransfer?'<label>Origen</label><select name="source_store"><option>BODEGA</option><option>DEVOLUCIONES</option></select><label>Destino</label><select name="destination_store"><option>DEVOLUCIONES</option><option>BODEGA</option></select>':kind.includes('PROVEEDOR')||kind.includes('BODEGA')?'<label>Almacén</label><select name="source_store"><option>BODEGA</option><option>DEVOLUCIONES</option></select>':''}</div><div class="ledger"><table class="data-table entry-table"><thead><tr><th>Clave revista</th><th>Nombre Revista</th><th>No.Edición</th><th>Precio</th><th>Cantidad</th><th>Descuento</th><th>Importe</th><th></th></tr></thead><tbody></tbody></table><button class="win-button add-line">＋ Partida</button></div><div class="totals"><div><span class="parts">Total de Partidas: 0</span><br><br><span class="copies">Total de Revistas: 0</span></div><div class="total-box"><label>Subtotal</label><input name="subtotal" value="$ 0.00" readonly><label>Descuento</label><input name="discount_total" value="$ 0.00" readonly><label>I.V.A.</label><input name="tax_total" value="$ 0.00" readonly><label>Total</label><input name="total" value="$ 0.00" readonly></div></div><div class="button-row"><button class="win-button save">💾 Guardar(F2)</button><button class="win-button close-op">🚪 Salir</button><button class="win-button another">📖 Dar de Alta Otra</button></div><div class="status-mini">${today()} &nbsp;&nbsp;&nbsp;&nbsp; Folio de la operación</div>`);
  const tbody=w.querySelector('tbody');
  const addLine=()=>{const tr=document.createElement('tr');tr.innerHTML='<td><input class="pub" size="10"></td><td class="title"></td><td><input class="edition" size="8"></td><td><input class="price" type="number" step="0.01" min="0"></td><td><input class="quantity" type="number" value="1" min="1"></td><td><input class="discount" type="number" value="0" min="0" max="100"></td><td class="amount">$0.00</td><td><button class="remove-line">×</button></td>';tbody.appendChild(tr);const lookup=async()=>{const pub=tr.querySelector('.pub').value,ed=tr.querySelector('.edition').value;if(!pub||!ed)return;const r=await fetch(`/api/edition-lookup?publication=${encodeURIComponent(pub)}&edition=${encodeURIComponent(ed)}`);const out=await r.json();if(!r.ok){toast(out.error);return}tr.dataset.editionId=out.id;tr.dataset.tax=out.tax;tr.querySelector('.title').textContent=out.title;tr.querySelector('.price').value=out.price;recalculate()};tr.querySelector('.pub').onchange=lookup;tr.querySelector('.edition').onchange=lookup;tr.querySelectorAll('input').forEach(i=>i.oninput=recalculate);tr.querySelector('.remove-line').onclick=()=>{tr.remove();recalculate()}};
  const recalculate=()=>{let subtotal=0,discountTotal=0,taxTotal=0,copies=0;tbody.querySelectorAll('tr').forEach(tr=>{const price=Number(tr.querySelector('.price').value||0),quantity=Number(tr.querySelector('.quantity').value||0),discount=Number(tr.querySelector('.discount').value||0),tax=Number(tr.dataset.tax||0),base=price*quantity,discounted=base*(1-discount/100),taxAmount=discounted*tax/100;subtotal+=base;discountTotal+=base-discounted;taxTotal+=taxAmount;copies+=quantity;tr.querySelector('.amount').textContent=money(discounted+taxAmount)});w.querySelector('.parts').textContent=`Total de Partidas: ${tbody.children.length}`;w.querySelector('.copies').textContent=`Total de Revistas: ${copies}`;w.querySelector('[name=subtotal]').value=money(subtotal);w.querySelector('[name=discount_total]').value=money(discountTotal);w.querySelector('[name=tax_total]').value=money(taxTotal);w.querySelector('[name=total]').value=money(subtotal-discountTotal+taxTotal)};
  w.querySelector('.add-line').onclick=addLine;w.querySelector('.close-op').onclick=()=>w.remove();w.querySelector('.another').onclick=()=>openOperation(kind);addLine();
  w.querySelector('.save').onclick=async()=>{const q=n=>w.querySelector(`[name=${n}]`)?.value||'';const items=[...tbody.querySelectorAll('tr')].map(tr=>({edition_id:tr.dataset.editionId,price:tr.querySelector('.price').value,quantity:tr.querySelector('.quantity').value,discount:tr.querySelector('.discount').value}));const data={kind,folio:q('folio'),operation_date:isoDate(q('operation_date')),party_code:q('party_code'),party_name:q('party_name'),sale_type:q('sale_type'),source_store:q('source_store'),destination_store:q('destination_store'),items};const r=await fetch('/api/documents',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const out=await r.json();if(r.ok){toast(`Movimiento ${out.id} guardado. Total ${money(out.total)}`);w.remove()}else toast(out.error||'No fue posible guardar el movimiento')};
}
function openReport(title){const w=win(title,true);w.insertAdjacentHTML('beforeend',`<div class="module-heading"><strong>CARLOS ESPINDOLA</strong><strong>${title}</strong></div><div class="form-area"><fieldset><legend>Parámetros del reporte</legend><div class="form-grid"><label>Fecha Inicial</label><input value="${today()}"><label>Fecha Final</label><input value="${today()}"><label>Clave Inicial</label><input><label>Clave Final</label><input></div></fieldset><p>Seleccione los parámetros para consultar la información.</p></div><div class="button-row"><button class="win-button" onclick="window.print()">🖨 Imprimir</button><button class="win-button close-report">🚪 Salir</button></div><div class="status-mini">${today()} &nbsp;&nbsp; ${title}</div>`);w.querySelector('.close-report').onclick=()=>w.remove()}
function openAbout(){const w=win('Acerca de SADYV',true);w.insertAdjacentHTML('beforeend',`<div class="form-area" style="text-align:center;padding-top:70px"><h2>SADYV</h2><p>SISTEMA DE ADMINISTRACION DISTRIBUCION Y VENTA DE REVISTAS</p><p>CARLOS ESPINDOLA</p><p>Versión Web local para Windows 11</p></div><div class="button-row"><button class="win-button close-about">Aceptar</button></div>`);w.querySelector('.close-about').onclick=()=>w.remove()}
function toast(msg){const t=document.createElement('div');t.className='toast';t.textContent=msg;document.querySelector('#desktop').appendChild(t);setTimeout(()=>t.remove(),2600)}
function format(v,key){if(v==null)return '';if(['balance','price','total'].includes(key))return Number(v).toLocaleString('es-MX',{style:'currency',currency:'MXN'});return String(v).replaceAll('&','&amp;').replaceAll('<','&lt;')}
function money(v){return Number(v||0).toLocaleString('es-MX',{style:'currency',currency:'MXN'})}
function today(){return document.body.dataset.today}function isoDate(d){const [a,m,y]=d.split('/');return `${y}-${m}-${a}`}
buildMenus();buildToolbar();setInterval(()=>document.querySelector('#clock').textContent=new Date().toLocaleTimeString('es-MX'),1000);
