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
const margin = { top: 20, right: 20, bottom: 50, left: 40 };
let zoom_value = 10
let zoom_refactor_val = 10
var dataElement = document.getElementById('data');
const summary_json = JSON.parse(dataElement.textContent || dataElement.innerText);


function svg_node_builder(summary_json,analytics_parameter){
    var width = 1100;
    var height = 300;
    let analytics_parameter_data = summary_json["analytics"][analytics_parameter]
    let keys = Object.keys(analytics_parameter_data)
    let values = Object.values(analytics_parameter_data)
    const data = []
    for (i=0;i<keys.length;i++){
        data.push({x:keys[i],y:values[i]})
    }
    let x = d3.scaleLinear()
    .domain([0, summary_json["number_of_iterations"]])
    .range([margin.left, width - margin.right]);

    let y = d3.scaleLinear()
        .domain([0, Math.max(...values)+10])
        .range([height - margin.bottom, margin.top]);

    let line = d3.line()
        .x(d => x(d.x))
        .y(d => y(d.y));

    let svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height);
    // Add zoom functionality
    let zoom = d3.zoom()
        .scaleExtent([1, 10])
        .on("zoom", zoomed);
    
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

    svg.append("path")
        .datum(data)
        .attr("class", "line")
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-width", 2)
        .attr("d", line);
    svg.selectAll(".plot-point")  // Correct class selector
        .data(data)
        .enter()
        .append("circle")
        .attr("class", "plot-point")  // Assign a class to the circles
        .attr("fill", "red")
        .attr("stroke", "none")
        .attr("cx", function (d) { return x(d.x) })
        .attr("cy", function (d) { return y(d.y) })
        .attr("r", 4)
        .on("mouseover", handleMouseOver)
        .on("mouseout", handleMouseOut);

    svg.call(zoom);
    
    function zoomed(event) {
        const newXScale = event.transform.rescaleX(x);
        const newYScale = event.transform.rescaleY(y);
        svg.select(".x-axis").call(d3.axisBottom(newXScale));
        svg.select(".line").attr("d", line.x(d => newXScale(d.x))
                                        .y(d => newYScale(d.y)));
        updateZoomLevel(event.transform.k);
        // Ensure that the y-axis is not affected by zoom
        y.range([height - margin.bottom, margin.top]);
        svg.select(".y-axis").call(d3.axisLeft(y));

        svg.selectAll(".plot-point")
            .attr("cx", d => newXScale(d.x))
            .attr("cy", d => newYScale(d.y));
            svg.select(".y-axis").call(d3.axisLeft(newYScale));
    }

    function updateZoomLevel(zoomLevel) {

        document.getElementById("zoomLevel").textContent = `Zoom Level: ${zoomLevel.toFixed(2)}`;
    }

    function handleMouseOver(event, d) {
        console.log("mouse")
        tooltip.transition()
            .duration(200)
            .style("opacity", .9);
        tooltip
            .html(`Iteration Number: ${d.x}<br> Value: ${d.y}`)
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

let analytics_parameters = Object.keys(summary_json["analytics"])
let svg_objects={}
analytics_parameters.forEach(analytics_element => {
    let svg_node=svg_node_builder(summary_json,analytics_element)
    let div_element=document.createElement("div");
    let heading =document.createElement("p")
    heading.textContent=analytics_element.toUpperCase()
    div_element.classList.add("graph_styling")
    div_element.appendChild(svg_node.svg.node())
    document.getElementById("container").appendChild(div_element);
    svg_objects[analytics_element]=svg_node
    div_element.appendChild(heading)
});



