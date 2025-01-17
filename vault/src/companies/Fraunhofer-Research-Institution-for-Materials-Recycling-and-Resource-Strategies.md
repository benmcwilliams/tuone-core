```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Fraunhofer Research Institution for Materials Recycling and Resource Strategies"
sort location, dt_announce desc
```
