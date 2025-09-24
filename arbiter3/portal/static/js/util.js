function getPlotParams(){
    let darkmode = (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
    
    let theme = "light";
    if (darkmode){
        theme = "dark";
    }

    return {"theme": theme}
}