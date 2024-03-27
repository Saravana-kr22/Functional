/**
 *
 * Copyright (c) 2023 Project CHIP Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
const margin = { top: 20, right: 20, bottom: 30, left: 90 };
let zoom_value = 10
var json_data
var svg_objects={}
var dataElement = document.getElementById('data');
var data_send=""
let data=JSON.parse(dataElement.textContent || dataElement.innerText)["graph_options"]
let tree = new Tree('.tree-container', {
    data: data,
    closeDepth: 3,
    onChange: function () {
        data_send=this.values
    }
})
async function printSelectedItems() {
    const divElements = document.querySelectorAll('.graph_styling');

// Loop through the div elements and clear their contents
    divElements.forEach((div) => {
    div.remove();
    });


    var selectedItems = data_send;
    
    let request_data=JSON.stringify({"fetch_data":selectedItems})
    let request_config={
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: request_data
      }
    let response = await fetch("/compareGraphData",request_config)
    if (response.status==200){
        json_data=await response.json()
        let params=Object.keys(json_data)
        let analtics_array=Object.values(json_data)
        for (let i=0;i<analtics_array.length;i++){
                let svg_node=svg_node_builder(analtics_array[i])
                let div_element=document.createElement("div");
                let heading =document.createElement("p")
                let graph_name = params[i]+"_option"
                let display_name=params[i].toUpperCase()
                heading.textContent=display_name
                div_element.classList.add("graph_styling")
                div_element.appendChild(svg_node.svg.node())
                document.getElementById("container").appendChild(div_element);
                svg_objects[graph_name]=svg_node
                div_element.appendChild(heading)
                // check_and_add_graph_options(graph_name,display_name)
                
            }
        }
}
// function check_and_add_graph_options(graph_name,display_name){
//     if (document.getElementById(graph_name)){
//         return 1
//     }
//     let select_tag=document.getElementById("analytics_options")
//     var opt=document.createElement("option")
//     opt.value=graph_name
//     opt.innerHTML = display_name;
//     opt.setAttribute("id",graph_name)
//     select_tag.appendChild(opt)
// }
function svg_node_builder(data){
        let zoom_refactor_val = Number(document.getElementById("zoom-refactor-edit").textContent)
        var width = 1250;
        var height = 500;
        var x = d3.scaleLinear()
        .domain([0, d3.max(data, function(d) { return +d.iteration_number; })])
        .range([margin.left, width - margin.right]);
        var y = d3.scaleLinear()
            .domain([0,d3.max(data, function(d) { return +d.value; })+10])
            .range([height - margin.bottom, margin.top]);
        // let sumstat=d3.group(data,d=>d.iteration)
        let svg = d3.create("svg")
            .attr("width", width)
            .attr("height", height);
        // Add zoom functionality
        let zoom = d3.zoom()
            .scaleExtent([1, zoom_refactor_val])
            .on("zoom", zoomed);
        let line = d3.line()
            .x(d => x(d.iteration_number))
            .y(d => y(d.value));
        // Group the data by iteration
        let nestedData = d3.group(data, d => d.iteration);
        
        let legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width - 400},0)`)  /* defines postion of the legend box */
        .style("font-size", "10px")
        .style("overflow-y", "auto")
        .style("max-height", "150px")

        // Generate random colors
        let legendIndex = 1;
        let colorScale = d3.scaleOrdinal(d3.schemeCategory10);            
        nestedData.forEach((values, key,i) => {
            let color = colorScale(key);
            console.log(color,key)
            svg.append("path")
                .datum(values)
                .attr("class", "line")
                .attr("fill", "none")
                .attr("stroke", color)
                .attr("stroke-width", 3)
                .attr("d", line);
            legend.append("rect")
                .attr("x", 0)
                .attr("y", legendIndex * 20)
                .attr("width", 10)
                .attr("height", 10)
                .attr("fill", color);
    
            legend.append("text")
                .attr("x", 15)
                .attr("y", legendIndex * 20 + 9)
                .text(`${key}`);
    
            legendIndex++;
        });
        let tooltip = d3.select("#container").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0)
            .style("background-color", "white")
            .style("border", "solid")
            .style("border-width", "2px")
            .style("border-radius", "5px")
            .style("padding", "5px")
            .style("position","absolute");
    
        svg.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${height - margin.bottom})`)
            .style("font","bold")
            .style("overflow","auto")
            .call(d3.axisBottom(x));
    
        svg.append("g")
            .attr("class", "y-axis")
            .style("overflow","auto")
            .attr("transform", `translate(${margin.left},0)`)
            .call(d3.axisLeft(y));
        svg.selectAll(".plot-point")  // Correct class selector
            .data(data)
            .enter()
            .append("circle")
            .attr("class", "plot-point")  // Assign a class to the circles
            .attr("fill", "red")
            .attr("stroke", "none")
            .attr("cx", function (d) { return x(d.iteration_number) })
            .attr("cy", function (d) { return y(d.value) })
            .attr("r", 4)
            .on("mouseover", handleMouseOver)
            .on("mouseout", handleMouseOut);
    
        svg.call(zoom);
        
        function zoomed(event) {
            const newXScale = event.transform.rescaleX(x);
            const newYScale = event.transform.rescaleY(y);
            
            svg.select(".x-axis").call(d3.axisBottom(newXScale));
            svg.selectAll(".line").attr("d", line.x(d => newXScale(d.iteration_number))
                                              .y(d => newYScale(d.value)))
            updateZoomLevel(event.transform.k);
            
            // Ensure that the y-axis is not affected by zoom
            y.range([height - margin.bottom, margin.top]);
            svg.select(".y-axis").call(d3.axisLeft(y));
    
            svg.selectAll(".plot-point")
                .attr("cx", d => newXScale(d.iteration_number))
                .attr("cy", d => newYScale(d.value));
            svg.select(".y-axis").call(d3.axisLeft(newYScale));
        }
    
        function updateZoomLevel(zoomLevel) {
    
            document.getElementById("zoomLevel").textContent = `Graph Zoom Level: ${zoomLevel.toFixed(2)}`;
        }
    
        function handleMouseOver(event, d) {
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            tooltip
                .html(`Iteration Number: ${d.iteration_number}<br>Value: ${d.value}<br>Iteration ID: ${d.iteration}`)
                .style("top", (event.pageY-100)+"px")
                .style("left",(event.pageX-100)+"px");
    
        }
    
        function handleMouseOut() {
    
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        }
        return {"svg":svg,"x":x,"y":y,"zoom":zoom,"line":line,"width":width,"height":height}
    }
function zoom_refactor() {
        let svg_array=Object.values(svg_objects)
        svg_array.forEach((svg_obj)=>{
        let zoom=svg_obj["zoom"]
        zoom.scaleExtent([1, Number(document.getElementById("zoom-refactor-edit").textContent)])
        })
}
document.addEventListener("DOMContentLoaded", function() {
    console.log("hi")
        var editIcon = document.getElementById("zoom-edit-button");
        editIcon.addEventListener("click", function(event) {
            console.log("hi")
            var inputDialog = document.createElement("div");
            inputDialog.innerHTML = '<input type="number" id="zoom-refactor-input" value="' + document.getElementById("zoom-refactor-edit").textContent + '"> <button id="save-btn" class="btn btn-primary sm">Save</button>';
            inputDialog.style.position = "absolute";
            inputDialog.style.left = (event.clientX + 10) + "px";
            inputDialog.style.top = (event.clientY + 10) + "px";
            inputDialog.style.background = "#fff";
            inputDialog.style.padding = "10px";
            inputDialog.style.border = "1px solid #ccc";
            inputDialog.style.boxShadow = "0 2px 4px rgba(0,0,0,0.1)";
            document.body.appendChild(inputDialog);
    
            var saveBtn = document.getElementById("save-btn");
            saveBtn.addEventListener("click", function() {
                var newValue = document.getElementById("zoom-refactor-input").value;
                document.getElementById("zoom-refactor-edit").textContent = newValue;
                zoom_refactor();
                inputDialog.remove();
            });
    
            // Close the dialog when clicking outside
            document.addEventListener("click", function(event) {
                if (!inputDialog.contains(event.target) && event.target !== editIcon) {
                    inputDialog.remove();
                }
            });
        });
    });
    
    