const translation = {
    en:{
        settings: 'settings'
    },
    ar:{
        settings: 'اعدادات'
    }
}

const languageSelect = document.getElementById("lang");

languageSelect.addEventListener('change', (event) => {
    setLang(event.target.value)
})

const setLang = (Language) => {
  const element = document.querySelectorAll("[data-i18n]");
  element.forEach((element) => {
    const translationKey = element.getAttribute("data-i18n");
    element.textContent = translation[Language][translationKey]
  });
  if(Language === "ar"){
    document.dir = "rtl";
  } else{
    document.dir = "ltr"
  }
}