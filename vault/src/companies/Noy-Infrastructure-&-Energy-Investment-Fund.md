```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Noy-Infrastructure-&-Energy-Investment-Fund" or company = "Noy Infrastructure & Energy Investment Fund")
sort location, dt_announce desc
```
