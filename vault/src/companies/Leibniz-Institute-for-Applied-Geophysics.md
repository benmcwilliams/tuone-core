```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Leibniz-Institute-for-Applied-Geophysics" or company = "Leibniz Institute for Applied Geophysics")
sort location, dt_announce desc
```
