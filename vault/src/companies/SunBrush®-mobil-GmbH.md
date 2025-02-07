```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "SunBrush®-mobil-GmbH" or company = "SunBrush® mobil GmbH")
sort location, dt_announce desc
```
