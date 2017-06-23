require(dplyr)
require(ggplot2)
require(reshape)

data <- read.csv("./r2_logs/w_optimal/02_23_2016/est_02_23_2016.csv")
names(data) <- c(names(data)[1:21], "E.Avg.cost.for.55.65", names(data)[22:(ncol(data)-1)])

min(data$fval)
min(data$Jtest)

rand_seed_list <- unique(data$rand.seed)

rand_seed <- rand_seed_list[1]

set_list <- list(set_1 = c('iter',
                            'Jtest', 
                            'dE.I.detect', 
                            'dE.beta.b.1',
                            'dE.beta.b.2',
                            'dE.beta.b.1.beta.b.2',
                            'dE.Avg.cost'),
                 set_2 = c('iter',
                            'Jtest', 
                            'dE.I.leave',
                            'dE.phat.I.leave'),
                 set_3 = c('iter',
                            'Jtest', 
                            'dE.I.detect.for.55.65',
                            'dE.beta.b.1.for.55.65',
                            'dE.beta.b.2.for.55.65'),
                           #,'dE.beta.b.1.beta.b.2.for.55.65'),
                           #,'dE.Avg.cost.for.55.65'),                      
                 params = c('iter', 
                             'Jtest', 
                             'g0',
                             'kappa0',
                             'kappa1',
                             'f1',
                             'f2',
                             'gamma'))
x_range  <- 100
for (rand_seed in rand_seed_list){
    data %>%
        filter(rand.seed == rand_seed) %>%
        arrange(desc(fval)) %>%
        distinct() %>%
        mutate(dE.I.detect = E.I.detect - E.I.detect.data,
               dE.beta.b.1 = E.beta.b.1 - E.beta.b.1.data, 
               dE.beta.b.2 = E.beta.b.2 - E.beta.b.2.data, 
               dE.beta.b.1.beta.b.2 = E.beta.b.1.beta.b.2 - E.beta.b.1.beta.b.2.data, 
               dE.Avg.cost = E.Avg.cost - E.Avg.cost.data, 
               dE.I.leave = E.I.leave - E.I.leave.data, 
               dE.phat.I.leave = E.phat.I.leave - E.phat.I.leave.data,
               dE.I.detect.for.55.65 = E.I.detect.for.55.65 - E.I.detect.for.55.65.data,
               dE.beta.b.1.for.55.65 = E.beta.b.1.for.55.65 - E.beta.b.1.for.55.65.data,
               dE.beta.b.2.for.55.65 = E.beta.b.2.for.55.65 - E.beta.b.2.for.55.65.data,
               #dE.beta.b.1.beta.b.2.for.55.65 = E.beta.b.1.beta.b.2.for.55.65 - E.beta.b.1.beta.b.2.for.55.65.data, 
               #dE.Avg.cost.for.55.65 = E.Avg.cost.for.55.65 - E.Avg.cost.for.55.65.data, 
               iter = 1:length(rand.seed)) -> jobs
    
    x_max <- max(jobs$iter)
    
    for (iset in 1:length(set_list)){
        set <- set_list[[iset]]
        melt(jobs[, set],  id.vars = 'iter', variable.name = 'series') %>%
            filter(iter > x_max - x_range & iter <= x_max) %>%
            ggplot(aes(iter, value)) + 
            geom_point(color = "#619CFF") + 
            facet_grid(variable ~ ., scales = "free_y") + 
            theme_bw() +
            geom_hline(aes(yintercept= 0), color = "#990000") +
            ggtitle(paste0('Random seed is ', rand_seed, ' with ', x_max, ' iterations (last ', x_range, ' iterations)'))
        ggsave(paste0('./r2_logs/w_optimal/02_23_2016/plot_', rand_seed, '_', names(set_list)[iset], '.pdf'), width = 8, heigh = 10)
    }
    
    # Bug in E.I.leave, E.phat.I.leave --- straight line!
    jobs %>%
        ggplot(aes(dE.I.leave, dE.phat.I.leave)) + 
        geom_point(color = "#619CFF")
}

# Test curvature for R1 ------------------------
# (-1e-1, -1e-2, -1e-3, -1e-4, 0, 1e-4, 1e-3, 1e-2, 1e-1)
fontsize <- 14

data <- read.csv('./r1_logs/grid_01_22_2016.csv')
data$rand.seed <- NULL

xopt <- as.numeric(data[1, 1:3])
fval_opt <- data$fval[1]
xopt_labels <- c('g', 'kappa0', 'kappa1')
for (i in 1:length(xopt)){
    xopt_label <- xopt_labels[i]
    not_i <- setdiff(1:length(xopt), i)
    ind <- which(abs(as.numeric(data[, not_i[1]]) - xopt[not_i[1]]) < 1e-5 
                 & abs(as.numeric(data[, not_i[2]]) - xopt[not_i[2]]) < 1e-5)
    
    # Set data to plot
    plot_data <- unique(data[ind, c(i, 4)])
    names(plot_data) <- c('x', 'fval')
    plot_data <- plot_data[order(plot_data$x), ]    
    plot_data$index_label <- c('-0.1', '-0.01', '-0.001', '-0.0001', '0', '0.0001', '0.001', '0.01', '0.1')
    plot_data$index <- 1:nrow(plot_data)
    plot_data$fval_rel  <- formatC(plot_data$fval/fval_opt, format = 'f', digits = 4) # relative fval
    
    # Get plot
    plot_data %>% # c(-1, -9)
        ggplot(aes(index, fval_rel, label = fval_rel)) + 
        geom_label(hjust = 0, nudge_x = 0.05, size = fontsize*0.3) + 
        geom_point(color = "#619CFF", size = 2) + 
        geom_point(aes(x = 5, y = fval_rel[5]), colour="#990000", size = 1) + 
        labs(x = xopt_label) + 
        scale_x_discrete(limits=plot_data$index_label) + 
        theme_bw() + 
        theme(plot.title = element_text(size=fontsize),
              axis.text=element_text(size=fontsize, color = 'black'),
              axis.title = element_text(size=fontsize, color = 'black'))
    ggsave(paste0('./r1_logs/deriv_step_', xopt_label, '.pdf'), width = 8, heigh = 8)    
}