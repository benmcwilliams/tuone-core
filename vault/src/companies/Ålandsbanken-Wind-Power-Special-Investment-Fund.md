```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ålandsbanken-Wind-Power-Special-Investment-Fund" or company = "Ålandsbanken Wind Power Special Investment Fund")
sort location, dt_announce desc
```
