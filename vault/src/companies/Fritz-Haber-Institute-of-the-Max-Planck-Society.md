```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Fritz-Haber-Institute-of-the-Max-Planck-Society" or company = "Fritz Haber Institute of the Max Planck Society")
sort location, dt_announce desc
```
