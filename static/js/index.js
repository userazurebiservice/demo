// Copyright (c) Microsoft Corporation.

/* 28-08-2024
$(function () {
    const reportContainer = $("#report-container").get(0);
  
    // Initialize iframe for embedding report
    powerbi.bootstrap(reportContainer, { type: "report"
   });
 
    const models = window["powerbi-client"].models;
    const reportLoadConfig = {
      type: "report",
      tokenType: models.TokenType.Embed,
    };

    
    fetch('/getembedinfo')
      .then(response => response.json())
      .then(embedData => {
        reportLoadConfig.accessToken = embedData.accessToken;
        reportLoadConfig.embedUrl = embedData.reportConfig[0].embedUrl;
        tokenExpiry = embedData.tokenExpiry;
  
        // Embed Power BI report using embedConfig
        var report = powerbi.embed(reportContainer, reportLoadConfig);
  
        // Event handlers for report loading and rendering
        report.on("loaded", function () {
          //console.log("Report load successful 1");
        });
  
        report.on("rendered", function () {
          //console.log("Report render successful");
        });
  
        // Error handling with detailed logging
        report.off("error"); // Clear existing error handler
        report.on("error", function (event) {
          var errorMsg = event.detail;
          //console.error("Error embedding report:", errorMsg);
        });
      })
      .catch(error => console.error("Error fetching embed info:", error));
  
  });
*/ 

  // ########### LCQ.09.08.2024 Este codigo antes estaba inserto en index.html ###############
  const reportContainer = document.getElementById('report-container');

  document.addEventListener('DOMContentLoaded', function() {
      fetch('/reports')
          .then(response => response.json())
          .then(data => {
              const reportList = document.getElementById('report-list');
              document.getElementById('group-name-display').textContent = "Todos";
              data.forEach(report => {
                  const listItem = document.createElement('li');
                  const link = document.createElement('a');
                  link.href = '#';
                  link.textContent = report.reportName;
                  link.addEventListener('click', () => {
                      document.getElementById('report-name-display').textContent = report.reportName; 
                      viewReport(report.reportId);
                  });
                  listItem.appendChild(link);
                  reportList.appendChild(listItem);
              });
          })
          .catch(error => console.error('Error fetching reports:', error));
  });

  function viewReport(reportId) {
  // 1. Mostrar un indicador de carga al usuario (opcional)

 const models = window["powerbi-client"].models;
  // 2. Realizar la solicitud al servidor para obtener la información de embebido del reporte
  
  fetch(`/viewreport/${reportId}`)
      .then(response => response.json())
      .then(embedInfo => {
      // 3. Extraer la información necesaria del objeto embedInfo
      const accessToken = embedInfo.accessToken;
      const embedUrl= embedInfo.reportConfig[0].embedUrl;
      const settings = embedInfo.settings || {}; // Configuración adicional (opcional)
     
      //MRC 26-08-2024
    /*  const reportName = embedInfo.reportConfig[0].reportName;
      document.getElementById('report-name-display').textContent = reportName;
      console.log(embedInfo) ;
    */
 

      // 4. Crear la configuración de embebido
      const config = {
          type: 'report',
          tokenType: models.TokenType.Embed,
          accessToken,
          embedUrl,
          settings
      };
      
      var report = powerbi.embed(reportContainer, config);
      report.innerHTML = ''; // Clear any existing report

      // 5. Actualizar el reporte embebido
          report.updateSettings(config)
          .then(() => {
          report.on("loaded", function () {
          });

          // 7. Manejar el evento de renderizado
          report.on('rendered', () => {
          });
          })

          .catch(error => {
          // 8. Manejar errores al actualizar el reporte
          console.error('Error al actualizar el reporte:', error);
          });
      })
      .catch(error => {

      });
  }


   // ######### MRC 28-08-2024 Funcionalidad de listado de grupos del usuario que inicio sesión ################
   document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_grupo')
    .then(response => response.json())
    .then(data => {
        const groupList = document.getElementById('grpusr-list');
        data.forEach(group => {
            const listItem = document.createElement('li');
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = group.grupo;
            link.addEventListener('click', () => {
              console.log('grupo seleccionado:  ',group.id_grupo);
              document.getElementById('group-name-display').textContent = group.grupo;
              get_reportg(group.id_grupo,group.grupo);
            });
            listItem.appendChild(link);
            groupList.appendChild(listItem);
        });
    })
    .catch(error => console.error('Error fetching groups:', error));
 
    }
  )
  ;

  //  document.addEventListener('DOMContentLoaded',
  function get_reportg(id_grupo,grupo) {
    console.log('Fetching report data for id:', id_grupo);
 
    fetch(`/get_reportg/${id_grupo}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        const reportList = document.getElementById('report-list');
        // Limpiar la lista antes de agregar nuevos elementos
        reportList.innerHTML = '';
        data.forEach(report => {
            const listItem = document.createElement('li');
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = report.reportName;
            link.addEventListener('click', () => {
              document.getElementById('report-name-display').textContent = report.reportName;
              document.getElementById('group-name-display').textContent = grupo;
              viewReport(report.reportId);
            });
            listItem.appendChild(link);
            reportList.appendChild(listItem);
 
        });
        console.log('reportList2: ',reportList)
      })
      .catch(error => console.error('Error fetching reports:', error));
 
 
  }

