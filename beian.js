/* 站点备案号 —— 换号只改下面这一个常量,全站页脚自动更新。
   用法:在页脚(.foot)后面加 <script src="./beian.js"></script>
   (栏目内页面用 ../beian.js,404 兜底页用 /beian.js)。 */
(function () {
  var BEIAN = '京ICP备13029686号-1';

  document.currentScript.insertAdjacentHTML('beforebegin',
    '<p style="text-align:center;font-size:.78rem;margin:4px 0 0;">' +
      '<a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener" ' +
         'style="color:#9A8C7C;text-decoration:none;">' + BEIAN + '</a></p>');
})();
