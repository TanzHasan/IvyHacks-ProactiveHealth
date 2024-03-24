"use client";

import { AxisBottom, AxisLeft } from "@visx/axis";
import { curveStepAfter } from "@visx/curve";
import { localPoint } from "@visx/event";
import { LinearGradient, RadialGradient } from "@visx/gradient";
import { MarkerCircle } from "@visx/marker";
import { Group } from "@visx/group";
import { Pattern } from "@visx/pattern";
import { ParentSize } from "@visx/responsive";
import { scaleLinear, scaleTime } from "@visx/scale";
import { AreaClosed, Bar, Circle, LinePath } from "@visx/shape";
import { TooltipWithBounds, useTooltip } from "@visx/tooltip";
import { bisector, extent } from "d3-array";

import { HealthKitRecord } from "@/utils/mongoquery";
import { time } from "console";

export type PatientChartProps = {
  hkHeartRateData: HealthKitRecord[];
  width: number;
  height: number;
};

const startAccessor = (record: HealthKitRecord) => new Date(record.start);
const endAccessor = (record: HealthKitRecord) => new Date(record.end);
const valueAccessor = (record: HealthKitRecord) => record.value;
const unitAccessor = (record: HealthKitRecord) => record.unit;

const margin = { top: 0, right: 0, bottom: 36, left: 36 };

export function HeartRateChart({
  hkHeartRateData,
  width,
  height,
}: PatientChartProps) {
  if (width <= 0 || height <= 0) {
    return null;
  }

  // bounds of the chart
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // scales
  const timeExtent = extent(hkHeartRateData, startAccessor);
  const timeScale = scaleTime({
    range: [0, innerWidth],
    domain: timeExtent as [Date, Date],
    round: true,
  });
  const valueExtent = extent(hkHeartRateData, valueAccessor);
  const valueScale = scaleLinear({
    range: [innerHeight, 0],
    domain: valueExtent as [number, number],
  });

  return (
    <svg width={width} height={height}>
      <Group top={margin.top} left={margin.left}>
        <MarkerCircle id="marker-circle" fill="#333" size={2} refX={2} />
        <AxisBottom top={innerHeight + 8} scale={timeScale} />
        <AxisLeft left={0} scale={valueScale} hideAxisLine hideTicks />
        <LinePath<HealthKitRecord>
          data={hkHeartRateData}
          x={(record) => timeScale(startAccessor(record))}
          y={(record) => valueScale(valueAccessor(record))}
          markerStart="url(#marker-circle)"
          markerMid="url(#marker-circle)"
          markerEnd="url(#marker-circle)"
        />
      </Group>
    </svg>
  );
}
