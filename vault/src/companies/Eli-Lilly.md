```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Eli-Lilly" or company = "Eli Lilly")
sort location, dt_announce desc
```
