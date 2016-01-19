# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
    v.cpus = 1
  end

  config.vm.box = "ubuntu/trusty64"

  config.vm.network "forwarded_port", guest: 3001, host: 3000
  config.vm.network "forwarded_port", guest: 5433, host: 5432
  config.vm.network "forwarded_port", guest: 8888, host: 8888


  config.vm.provision :shell, :path => "provision.sh", 
    :run => "always", :privileged => false
  
end
